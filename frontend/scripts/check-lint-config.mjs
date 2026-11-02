import assert from 'node:assert/strict';
import {
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';
import { getTypeDiagnostics, readProjectConfig } from './check-types.mjs';
import {
  ruleExamples,
  scopeExamples,
  optionExamples,
  componentNameExamples,
} from './lint-examples.mjs';

const projectRoot = fileURLToPath(new URL('../', import.meta.url));
const packageJson = JSON.parse(
  readFileSync(path.join(projectRoot, 'package.json'), 'utf8')
);
// This command has plain arguments, not shell operators or quoted expressions.
const lintCommand = packageJson.scripts['lint:js'];
assert.match(lintCommand, /^[\w./=:\s-]+$/);
const lintArguments = lintCommand.trim().split(/\s+/);
assert.equal(lintArguments.shift(), 'oxlint');
assert.equal(lintArguments.pop(), '.');
const temporaryProjects = [];
after(() => {
  for (const directory of temporaryProjects) {
    rmSync(directory, { recursive: true, force: true });
  }
});

function createProject() {
  const directory = mkdtempSync(path.join(tmpdir(), 'story-filler-lint-'));
  temporaryProjects.push(directory);
  symlinkSync(
    path.join(projectRoot, 'node_modules'),
    path.join(directory, 'node_modules'),
    'dir'
  );
  // Copy the real configuration unchanged; file paths keep the same scopes.
  for (const name of ['oxlint.config.mjs', 'jsconfig.json']) {
    copyFileSync(path.join(projectRoot, name), path.join(directory, name));
  }
  return directory;
}

function writeSource(directory, name, code) {
  const file = path.join(directory, name);
  mkdirSync(path.dirname(file), { recursive: true });
  writeFileSync(file, code);
  return file;
}

const directory = createProject();
const fixtures = [];
function fixture(name, code, engine = 'oxlint') {
  // This exact path is itself a configuration boundary, so keep its name.
  const uniqueName =
    name === 'src/setupTests.js'
      ? name
      : path.join(
          path.dirname(name),
          `${fixtures.length}-${path.basename(name)}`
        );
  const result = {
    name: uniqueName,
    file: writeSource(directory, uniqueName, code),
    engine,
  };
  fixtures.push(result);
  return result;
}

const pairs = ruleExamples.map((example) => ({
  ...example,
  invalidFixture: fixture(example.file, example.invalid, example.engine),
  validFixture: fixture(example.file, example.valid, example.engine),
}));
const scopes = scopeExamples.map((example) => ({
  ...example,
  fixture: fixture(example.file, example.code),
}));
const options = optionExamples.map((example) => ({
  ...example,
  fixture: fixture(example.file, example.code),
}));
const componentNames = componentNameExamples.map((example) => ({
  ...example,
  fixture: fixture('src/component-name.jsx', example.code, 'typescript'),
}));

// One native process and one TypeScript program cover the fixture set.
// No rules are disabled for individual examples; libraries load only once.
const lintFixtures = fixtures.filter((item) => item.engine === 'oxlint');
function runOxlint(root, files = ['.']) {
  const result = spawnSync(
    process.execPath,
    [
      path.join(projectRoot, 'node_modules/oxlint/bin/oxlint'),
      ...lintArguments,
      '--format',
      'json',
      ...files,
    ],
    { cwd: root, encoding: 'utf8', timeout: 30_000, maxBuffer: 8_000_000 }
  );
  assert.ifError(result.error);
  assert.ok([0, 1].includes(result.status), result.stderr);
  return { status: result.status, report: JSON.parse(result.stdout) };
}
const { report: lintReport } = runOxlint(
  directory,
  lintFixtures.map((item) => item.name)
);
assert.equal(lintReport.number_of_files, lintFixtures.length);
assert.ok(Array.isArray(lintReport.diagnostics));

const typedFixtures = fixtures.filter((item) => item.engine === 'typescript');
const config = readProjectConfig(directory);
assert.deepEqual(config.errors, []);
const compilerHost = ts.createCompilerHost(config.options);
compilerHost.getCurrentDirectory = () => directory;
const program = ts.createProgram(
  typedFixtures.map((item) => item.file),
  config.options,
  compilerHost
);
const typeDiagnostics = getTypeDiagnostics(program);
const typedFiles = new Set(typedFixtures.map((item) => item.file));
assert.deepEqual(
  typeDiagnostics
    .filter((diagnostic) => !typedFiles.has(diagnostic.file?.fileName))
    .map((diagnostic) =>
      ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')
    ),
  []
);

function diagnosticsFor(item) {
  if (item.engine === 'typescript') {
    return typeDiagnostics
      .filter((diagnostic) => diagnostic.file?.fileName === item.file)
      .map((diagnostic) => ({
        code: diagnostic.code,
        severity:
          diagnostic.category === ts.DiagnosticCategory.Error
            ? 'error'
            : 'warning',
        message: ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n'),
      }));
  }
  return lintReport.diagnostics.filter(
    (diagnostic) => path.resolve(directory, diagnostic.filename) === item.file
  );
}

function oxlintCode(rule) {
  const separator = rule.indexOf('/');
  return separator === -1
    ? `eslint(${rule})`
    : `${rule.slice(0, separator)}(${rule.slice(separator + 1)})`;
}

for (const example of pairs) {
  test(`${example.rule} rejects its invalid example`, () => {
    const diagnostics = diagnosticsFor(example.invalidFixture);
    assert.ok(
      diagnostics.some((diagnostic) => {
        if (diagnostic.severity !== 'error') return false;
        if (example.parserMessage) {
          // Only this reviewed syntax error counts, not arbitrary parse failure.
          return (
            !diagnostic.code && diagnostic.message === example.parserMessage
          );
        }
        const expected =
          example.diagnosticCode ??
          oxlintCode(example.expectedRule ?? example.rule);
        return diagnostic.code === expected;
      }),
      JSON.stringify(diagnostics)
    );
  });
  test(`${example.rule} accepts its valid example`, () => {
    assert.deepEqual(diagnosticsFor(example.validFixture), []);
  });
}

for (const [group, examples] of [
  ['scope', scopes],
  ['option', options],
]) {
  for (const example of examples) {
    test(`${group}: ${example.name}`, () => {
      const diagnostics = diagnosticsFor(example.fixture);
      if (example.expectedRule === null) {
        assert.deepEqual(diagnostics, []);
      } else {
        assert.ok(
          diagnostics.some(
            (diagnostic) =>
              diagnostic.severity === 'error' &&
              diagnostic.code === oxlintCode(example.expectedRule)
          ),
          JSON.stringify(diagnostics)
        );
      }
    });
  }
}

for (const example of componentNames) {
  test(`React wrapper names: ${example.name}`, () => {
    const diagnostics = diagnosticsFor(example.fixture);
    if (example.invalid) {
      assert.equal(diagnostics.length, 1, JSON.stringify(diagnostics));
      assert.equal(diagnostics[0].code, 95001);
      assert.equal(diagnostics[0].severity, 'error');
    } else {
      assert.deepEqual(diagnostics, []);
    }
  });
}

function runProductionTypeCheck(prepare) {
  const root = createProject();
  writeSource(root, 'src/main.js', 'export const value = 1;');
  for (const name of ['check-types.mjs', 'lint-component-names.mjs']) {
    writeSource(
      root,
      `scripts/${name}`,
      readFileSync(path.join(projectRoot, 'scripts', name), 'utf8')
    );
  }
  prepare(root);
  return spawnSync(process.execPath, ['scripts/check-types.mjs'], {
    cwd: root,
    encoding: 'utf8',
    timeout: 30_000,
    maxBuffer: 2_000_000,
  });
}

test('production type-check command accepts its application and lint-only scopes', () => {
  const result = runProductionTypeCheck((root) => {
    writeSource(
      root,
      'src/example.test.jsx',
      'export function Fixture({ value }) { return <p>{value}</p>; }'
    );
    writeSource(root, 'scripts/helper.cjs', 'module.exports = value => value;');
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
});

for (const [name, code, prepare] of [
  [
    'configuration errors',
    5024,
    (root) => {
      const settings = JSON.parse(
        readFileSync(path.join(root, 'jsconfig.json'), 'utf8')
      );
      settings.compilerOptions.strict = 'invalid';
      writeSource(root, 'jsconfig.json', JSON.stringify(settings));
    },
  ],
  [
    'application type errors',
    2322,
    (root) =>
      writeSource(
        root,
        'src/main.js',
        '/** @type {string} */\nexport const value = 1;'
      ),
  ],
  [
    'legacy CommonJS octal syntax',
    1121,
    (root) => writeSource(root, 'scripts/legacy.cjs', 'module.exports = 071;'),
  ],
]) {
  test(`production type-check command fails for ${name}`, () => {
    const result = runProductionTypeCheck(prepare);
    assert.ifError(result.error);
    assert.equal(result.status, 1, result.stderr);
    assert.match(result.stderr, new RegExp(`TS${code}\\b`));
  });
}

function runProductionLint(prepare) {
  const root = createProject();
  writeSource(root, 'src/main.js', 'export const value = 1;');
  prepare(root);
  return runOxlint(root);
}

test('production lint command discovers source and ignores generated assets', () => {
  const result = runProductionLint((root) => {
    writeSource(
      root,
      'dist/assets/generated.js',
      'debugger; unknownVariable();'
    );
  });
  assert.equal(result.status, 0, JSON.stringify(result.report.diagnostics));
  assert.deepEqual(result.report.diagnostics, []);
});

test('production lint command rejects an unused suppression', () => {
  const result = runProductionLint((root) => {
    writeSource(
      root,
      'src/main.js',
      '// eslint-disable-next-line no-debugger\nexport const value = 1;'
    );
  });
  assert.equal(result.status, 1);
  assert.ok(
    result.report.diagnostics.some(
      (item) =>
        item.severity === 'error' &&
        item.message ===
          'Unused eslint-disable directive (no problems were reported).'
    ),
    JSON.stringify(result.report.diagnostics)
  );
});

test('production lint command discovers invalid nested source files', () => {
  const result = runProductionLint((root) => {
    writeSource(root, 'src/nested/problem.js', 'debugger;');
  });
  assert.equal(result.status, 1);
  assert.ok(
    result.report.diagnostics.some(
      (item) => item.code === 'eslint(no-debugger)' && item.severity === 'error'
    ),
    JSON.stringify(result.report.diagnostics)
  );
});

test('nested configuration cannot disable the project lint checks', () => {
  const result = runProductionLint((root) => {
    writeSource(root, 'src/nested/problem.js', 'debugger;');
    writeSource(
      root,
      'src/nested/.oxlintrc.json',
      JSON.stringify({ rules: { 'no-debugger': 'off' } })
    );
  });
  assert.equal(result.status, 1);
  assert.ok(
    result.report.diagnostics.some(
      (item) => item.code === 'eslint(no-debugger)' && item.severity === 'error'
    ),
    JSON.stringify(result.report.diagnostics)
  );
});
