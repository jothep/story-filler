// Run the full-tree npm audit and fail on any advisory not in
// audit-allowlist.json. The production audit (`npm audit --omit=dev`) stays a
// separate zero-tolerance check and does not read this allowlist.
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { evaluateAudit } from './npm-audit.mjs';

const allowlistUrl = new URL('../audit-allowlist.json', import.meta.url);

function main() {
  const audit = spawnSync('npm', ['audit', '--json'], {
    cwd: new URL('..', import.meta.url),
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
    shell: process.platform === 'win32',
  });
  if (audit.error) throw audit.error;

  let report;
  try {
    report = JSON.parse(audit.stdout);
  } catch {
    throw new Error(`npm audit did not return JSON:\n${audit.stderr}`);
  }
  if (report.error) {
    throw new Error(`npm audit failed: ${JSON.stringify(report.error)}`);
  }

  const allowlist = JSON.parse(readFileSync(allowlistUrl, 'utf8'));
  const { blocked, allowed, unused } = evaluateAudit(report, allowlist);

  for (const advisory of allowed) {
    console.log(
      `Allowed by audit-allowlist.json: ${advisory.id} (${advisory.package}, ${advisory.severity})`
    );
  }
  for (const entry of unused) {
    console.log(
      `No longer reported: ${entry.id} (${entry.package}). Remove it from audit-allowlist.json.`
    );
  }
  if (blocked.length) {
    for (const advisory of blocked) {
      console.error(
        `Blocked: ${advisory.id} (${advisory.package}, ${advisory.severity}) ${advisory.title}`
      );
    }
    process.exitCode = 1;
    return;
  }
  console.log('Full-tree audit: no advisories outside the allowlist.');
}

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
}
