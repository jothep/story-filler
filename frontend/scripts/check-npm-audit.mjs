import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { evaluateAudit, readAllowlist } from './npm-audit.mjs';

const PICOMATCH = 'GHSA-fc5q-39xc-vjpf';

function advisory(id, name, severity = 'high') {
  return {
    source: 1,
    name,
    dependency: name,
    title: `${name} finding`,
    url: `https://github.com/advisories/${id}`,
    severity,
    range: '<=1.0.0',
  };
}

// Mirrors the shape npm 11 reports for the picomatch chain.
function report(extra = {}) {
  const vulnerabilities = {
    picomatch: { severity: 'high', via: [advisory(PICOMATCH, 'picomatch')] },
    fdir: { severity: 'high', via: ['picomatch'] },
    tinyglobby: { severity: 'high', via: ['fdir', 'picomatch'] },
    vite: { severity: 'high', via: ['fdir', 'picomatch', 'tinyglobby'] },
    vitest: { severity: 'high', via: ['picomatch', 'tinyglobby'] },
    ...extra,
  };
  return {
    auditReportVersion: 2,
    vulnerabilities,
    metadata: {
      vulnerabilities: { total: Object.keys(vulnerabilities).length },
    },
  };
}

const allowlist = {
  advisories: [
    {
      id: PICOMATCH,
      package: 'picomatch',
      recorded: '2026-11-18',
      reason: 'No patched release; build and test only.',
    },
  ],
};

test('an allowlisted advisory and its dependency paths pass', () => {
  const result = evaluateAudit(report(), allowlist);
  assert.deepEqual(result.blocked, []);
  assert.deepEqual(
    result.allowed.map((item) => item.id),
    [PICOMATCH]
  );
  assert.deepEqual(result.unused, []);
});

test('any other advisory is blocked, whatever its severity', () => {
  for (const severity of ['low', 'moderate', 'high', 'critical']) {
    const result = evaluateAudit(
      report({
        lodash: {
          severity,
          via: [advisory('GHSA-aaaa-bbbb-cccc', 'lodash', severity)],
        },
      }),
      allowlist
    );
    assert.deepEqual(
      result.blocked.map((item) => item.id),
      ['GHSA-aaaa-bbbb-cccc']
    );
  }
});

test('the same advisory id on another package is blocked', () => {
  const result = evaluateAudit(
    report({ micromatch: { via: [advisory(PICOMATCH, 'micromatch')] } }),
    allowlist
  );
  assert.deepEqual(
    result.blocked.map((item) => item.package),
    ['micromatch']
  );
});

test('a clean report passes and flags the entry for removal', () => {
  const clean = {
    auditReportVersion: 2,
    vulnerabilities: {},
    metadata: { vulnerabilities: { total: 0 } },
  };
  const result = evaluateAudit(clean, allowlist);
  assert.deepEqual(result.blocked, []);
  assert.deepEqual(
    result.unused.map((item) => item.id),
    [PICOMATCH]
  );
});

test('unclear reports fail closed', () => {
  const broken = [
    null,
    { auditReportVersion: 1, vulnerabilities: {} },
    { ...report(), metadata: { vulnerabilities: { total: 99 } } },
    report({ orphan: { via: ['not-reported'] } }),
    report({ empty: { via: [] } }),
    report({ odd: { via: [{ name: 'odd', url: 'https://example.com/x' }] } }),
  ];
  for (const input of broken) {
    assert.throws(() => evaluateAudit(input, allowlist));
  }
});

test('dependency paths that never reach an advisory fail closed', () => {
  const cycleOnly = {
    auditReportVersion: 2,
    vulnerabilities: { a: { via: ['b'] }, b: { via: ['a'] } },
    metadata: { vulnerabilities: { total: 2 } },
  };
  assert.throws(
    () => evaluateAudit(cycleOnly, allowlist),
    /does not lead to an advisory/
  );
  // A cycle beside the allowed picomatch chain must not hide behind it.
  assert.throws(
    () =>
      evaluateAudit(
        report({ a: { via: ['b'] }, b: { via: ['a'] } }),
        allowlist
      ),
    /does not lead to an advisory/
  );
  // A cycle that does reach an advisory is still a valid report.
  assert.doesNotThrow(() =>
    evaluateAudit(
      report({ a: { via: ['b', 'picomatch'] }, b: { via: ['a'] } }),
      allowlist
    )
  );
});

test('allowlist entries need an id, package, date and reason', () => {
  const base = allowlist.advisories[0];
  for (const change of [
    { id: 'CVE-2026-1' },
    { package: '' },
    { recorded: '18/11/2026' },
    { recorded: '2026-99-99' },
    { recorded: '2026-02-30' },
    { reason: ' ' },
  ]) {
    assert.throws(() =>
      readAllowlist({ advisories: [{ ...base, ...change }] })
    );
  }
  assert.throws(() => readAllowlist({ advisories: [base, base] }));
  assert.throws(() => readAllowlist({}));
});

test('the committed allowlist is valid', () => {
  const committed = JSON.parse(
    readFileSync(new URL('../audit-allowlist.json', import.meta.url), 'utf8')
  );
  assert.doesNotThrow(() => readAllowlist(committed));
});
