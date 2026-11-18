// Evaluate an `npm audit --json` report against a reviewed advisory allowlist.
// Anything the report or allowlist does not state clearly is rejected.

const ADVISORY_URL =
  /^https:\/\/github\.com\/advisories\/(GHSA(?:-[0-9a-z]{4}){3})$/;
const ADVISORY_ID = /^GHSA(?:-[0-9a-z]{4}){3}$/;

// Accept only real calendar dates, so 2026-02-30 or 2026-99-99 is rejected.
function isCalendarDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }
  const date = new Date(`${value}T00:00:00Z`);
  return (
    !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value
  );
}

export function readAllowlist(data) {
  if (!data || !Array.isArray(data.advisories)) {
    throw new Error('Allowlist must contain an advisories array');
  }
  const seen = new Set();
  return data.advisories.map((entry, index) => {
    const where = `Allowlist entry ${index + 1}`;
    if (!entry || typeof entry !== 'object') {
      throw new Error(`${where} must be an object`);
    }
    const { id, package: name, recorded, reason } = entry;
    if (typeof id !== 'string' || !ADVISORY_ID.test(id)) {
      throw new Error(`${where} needs a GHSA advisory id`);
    }
    if (typeof name !== 'string' || !name) {
      throw new Error(`${where} needs the affected package name`);
    }
    if (!isCalendarDate(recorded)) {
      throw new Error(`${where} needs a recorded date (YYYY-MM-DD)`);
    }
    if (typeof reason !== 'string' || !reason.trim()) {
      throw new Error(`${where} needs a reason`);
    }
    const key = `${id} ${name}`;
    if (seen.has(key)) throw new Error(`${where} repeats ${key}`);
    seen.add(key);
    return { id, package: name };
  });
}

export function readAdvisories(report) {
  if (
    !report ||
    report.auditReportVersion !== 2 ||
    !report.vulnerabilities ||
    typeof report.vulnerabilities !== 'object'
  ) {
    throw new Error('Expected an npm audit report (auditReportVersion 2)');
  }
  const vulnerable = report.vulnerabilities;
  const advisories = [];
  const paths = new Map();
  const sourced = new Set();
  for (const [name, entry] of Object.entries(vulnerable)) {
    if (!entry || !Array.isArray(entry.via) || entry.via.length === 0) {
      throw new Error(`Vulnerability ${name} has no source`);
    }
    paths.set(name, []);
    for (const source of entry.via) {
      if (typeof source === 'string') {
        // A dependency path: the named package must carry its own finding.
        if (!Object.hasOwn(vulnerable, source)) {
          throw new Error(`Vulnerability ${name} cites unreported ${source}`);
        }
        paths.get(name).push(source);
        continue;
      }
      sourced.add(name);
      const match = ADVISORY_URL.exec(source?.url ?? '');
      if (!match || typeof source.name !== 'string') {
        throw new Error(`Vulnerability ${name} has an unidentified advisory`);
      }
      advisories.push({
        id: match[1],
        package: source.name,
        severity: String(source.severity),
        title: String(source.title ?? ''),
      });
    }
  }
  // Every finding must reach an advisory. A cycle of dependency paths with no
  // advisory would otherwise contribute nothing and pass unnoticed.
  let changed = true;
  while (changed) {
    changed = false;
    for (const [name, via] of paths) {
      if (!sourced.has(name) && via.some((source) => sourced.has(source))) {
        sourced.add(name);
        changed = true;
      }
    }
  }
  for (const name of paths.keys()) {
    if (!sourced.has(name)) {
      throw new Error(`Vulnerability ${name} does not lead to an advisory`);
    }
  }

  const total = report.metadata?.vulnerabilities?.total;
  if (total !== Object.keys(vulnerable).length) {
    throw new Error('Audit metadata does not match the reported packages');
  }
  return advisories;
}

export function evaluateAudit(report, allowlistData) {
  const allowlist = readAllowlist(allowlistData);
  const advisories = readAdvisories(report);
  const isAllowed = (advisory) =>
    allowlist.some(
      (entry) => entry.id === advisory.id && entry.package === advisory.package
    );
  const unique = (items) => [
    ...new Map(
      items.map((item) => [`${item.id} ${item.package}`, item])
    ).values(),
  ];
  return {
    blocked: unique(advisories.filter((advisory) => !isAllowed(advisory))),
    allowed: unique(advisories.filter(isAllowed)),
    unused: allowlist.filter(
      (entry) =>
        !advisories.some(
          (advisory) =>
            advisory.id === entry.id && advisory.package === entry.package
        )
    ),
  };
}
