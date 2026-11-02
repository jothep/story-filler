import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';
import { getComponentNameDiagnostics } from './lint-component-names.mjs';

export function readProjectConfig(projectRoot) {
  const configPath = path.join(projectRoot, 'jsconfig.json');
  const config = ts.readConfigFile(configPath, ts.sys.readFile);
  if (config.error) {
    return { errors: [config.error], fileNames: [], options: {} };
  }
  return ts.parseJsonConfigFileContent(config.config, ts.sys, projectRoot);
}

export function getTypeDiagnostics(program) {
  return [
    ...ts.getPreEmitDiagnostics(program),
    ...getComponentNameDiagnostics(program),
  ];
}

export function getProjectDiagnostics(projectRoot) {
  const config = readProjectConfig(projectRoot);
  if (config.errors.length) return config.errors;

  const program = ts.createProgram(config.fileNames, config.options);
  const diagnostics = getTypeDiagnostics(program);

  // Node scripts and test fixtures keep their existing lint-only scope. Still
  // reject syntax such as legacy octal literals, which Oxlint permits in CJS.
  const otherFiles = ts.sys
    .readDirectory(
      projectRoot,
      ['.js', '.jsx', '.mjs', '.cjs'],
      ['node_modules', 'dist', '.git'],
      ['**/*']
    )
    .filter((file) => !program.getSourceFile(file));
  const syntaxProgram = ts.createProgram(otherFiles, {
    allowJs: true,
    noEmit: true,
    noResolve: true,
    noLib: true,
    target: ts.ScriptTarget.ESNext,
    jsx: ts.JsxEmit.Preserve,
  });
  return [...diagnostics, ...syntaxProgram.getSyntacticDiagnostics()];
}

const projectRoot = fileURLToPath(new URL('../', import.meta.url));
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const diagnostics = getProjectDiagnostics(projectRoot);
  if (diagnostics.length) {
    console.error(
      ts.formatDiagnosticsWithColorAndContext(diagnostics, {
        getCurrentDirectory: () => projectRoot,
        getCanonicalFileName: (file) => file,
        getNewLine: () => '\n',
      })
    );
    process.exitCode = 1;
  }
}
