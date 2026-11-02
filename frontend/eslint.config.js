import globals from 'globals';
import javascript from '@eslint/js';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';

const sourceFiles = ['src/**/*.{js,jsx}'];
const testFiles = [
  'src/**/*.{test,spec}.{js,jsx}',
  'src/setupTests.js',
  'src/testUtils/**/*.{js,jsx}',
];
const jsxParserOptions = { ecmaFeatures: { jsx: true } };

export default [
  {
    name: 'generated-files',
    ignores: ['dist/**', 'node_modules/**'],
  },
  {
    ...javascript.configs.recommended,
    name: 'javascript',
    files: ['**/*.{js,jsx,mjs,cjs}'],
  },
  {
    name: 'browser-application',
    files: sourceFiles,
    ignores: testFiles,
    languageOptions: {
      globals: globals.browser,
      parserOptions: jsxParserOptions,
    },
    plugins: { react, 'react-hooks': reactHooks },
    settings: { react: { version: 'detect' } },
    rules: {
      ...react.configs.recommended.rules,
      ...react.configs['jsx-runtime'].rules,
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',
    },
  },
  {
    name: 'node-tooling',
    files: ['*.config.{js,mjs,cjs}', 'scripts/**/*.{js,mjs,cjs}'],
    languageOptions: { globals: globals.node },
  },
  {
    name: 'vitest-and-test-helpers',
    files: testFiles,
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
      parserOptions: jsxParserOptions,
    },
    // Test components and mocks are fixtures, not application component APIs.
    // Keep JSX name checks and require explicit imports of Vitest's test APIs.
    plugins: { react },
    rules: {
      'react/jsx-uses-vars': 'error',
      'react/jsx-no-undef': 'error',
    },
  },
];
