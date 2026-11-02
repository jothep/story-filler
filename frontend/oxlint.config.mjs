import globals from 'globals';

// Preserve the reviewed JavaScript checks; do not enable new category presets.
// Duplicate arguments are rejected by the parser/no-redeclare. The separate
// syntax check also rejects legacy octal literals in CommonJS files.
// JSX references are tracked natively; checkJs covers component prop contracts
// and removed React APIs. no-unsafe also checks the old lifecycle aliases.
export default {
  plugins: ['react'],
  categories: {
    correctness: 'off',
  },
  ignorePatterns: ['dist/**', 'node_modules/**'],
  rules: {
    'eslint/constructor-super': [2],
    'eslint/for-direction': [2],
    'eslint/getter-return': [
      2,
      {
        allowImplicit: false,
      },
    ],
    'eslint/no-async-promise-executor': [2],
    'eslint/no-case-declarations': [2],
    'eslint/no-class-assign': [2],
    'eslint/no-compare-neg-zero': [2],
    'eslint/no-cond-assign': [2, 'except-parens'],
    'eslint/no-const-assign': [2],
    'eslint/no-constant-binary-expression': [2],
    'eslint/no-constant-condition': [
      2,
      {
        checkLoops: 'allExceptWhileTrue',
      },
    ],
    'eslint/no-control-regex': [2],
    'eslint/no-debugger': [2],
    'eslint/no-delete-var': [2],
    'eslint/no-dupe-class-members': [2],
    'eslint/no-dupe-else-if': [2],
    'eslint/no-dupe-keys': [2],
    'eslint/no-duplicate-case': [2],
    'eslint/no-empty': [
      2,
      {
        allowEmptyCatch: false,
      },
    ],
    'eslint/no-empty-character-class': [2],
    'eslint/no-empty-pattern': [
      2,
      {
        allowObjectPatternsAsParameters: false,
      },
    ],
    'eslint/no-empty-static-block': [2],
    'eslint/no-ex-assign': [2],
    'eslint/no-extra-boolean-cast': [2, {}],
    'eslint/no-fallthrough': [
      2,
      {
        allowEmptyCase: false,
        reportUnusedFallthroughComment: false,
      },
    ],
    'eslint/no-func-assign': [2],
    'eslint/no-global-assign': [
      2,
      {
        exceptions: [],
      },
    ],
    'eslint/no-import-assign': [2],
    'eslint/no-invalid-regexp': [2, {}],
    'eslint/no-irregular-whitespace': [
      2,
      {
        skipComments: false,
        skipJSXText: false,
        skipRegExps: false,
        skipStrings: true,
        skipTemplates: false,
      },
    ],
    'eslint/no-loss-of-precision': [2],
    'eslint/no-misleading-character-class': [
      2,
      {
        allowEscape: false,
      },
    ],
    'eslint/no-new-native-nonconstructor': [2],
    'eslint/no-nonoctal-decimal-escape': [2],
    'eslint/no-obj-calls': [2],
    'eslint/no-prototype-builtins': [2],
    'eslint/no-redeclare': [
      2,
      {
        builtinGlobals: true,
      },
    ],
    'eslint/no-regex-spaces': [2],
    'eslint/no-self-assign': [
      2,
      {
        props: true,
      },
    ],
    'eslint/no-setter-return': [2],
    'eslint/no-shadow-restricted-names': [
      2,
      {
        reportGlobalThis: false,
      },
    ],
    'eslint/no-sparse-arrays': [2],
    'eslint/no-this-before-super': [2],
    'eslint/no-undef': [
      2,
      {
        typeof: false,
      },
    ],
    'eslint/no-unexpected-multiline': [2],
    'eslint/no-unreachable': [2],
    'eslint/no-unsafe-finally': [2],
    'eslint/no-unsafe-negation': [
      2,
      {
        enforceForOrderingRelations: false,
      },
    ],
    'eslint/no-unsafe-optional-chaining': [
      2,
      {
        disallowArithmeticOperators: false,
      },
    ],
    'eslint/no-unused-labels': [2],
    'eslint/no-unused-private-class-members': [2],
    'eslint/no-unused-vars': [2],
    'eslint/no-useless-backreference': [2],
    'eslint/no-useless-catch': [2],
    'eslint/no-useless-escape': [
      2,
      {
        allowRegexCharacters: [],
      },
    ],
    'eslint/no-with': [2],
    'eslint/require-yield': [2],
    'eslint/use-isnan': [
      2,
      {
        enforceForIndexOf: false,
        enforceForSwitchCase: true,
      },
    ],
    'eslint/valid-typeof': [
      2,
      {
        requireStringLiterals: false,
      },
    ],
  },
  overrides: [
    {
      files: ['src/**/*.{js,jsx}'],
      excludeFiles: [
        'src/**/*.{test,spec}.{js,jsx}',
        'src/setupTests.js',
        'src/testUtils/**/*.{js,jsx}',
      ],
      globals: globals.browser,
      rules: {
        'react/display-name': [2],
        'react/jsx-key': [2],
        'react/jsx-no-comment-textnodes': [2],
        'react/jsx-no-duplicate-props': [2],
        'react/jsx-no-target-blank': [2],
        'react/jsx-no-undef': [2],
        'react/no-children-prop': [2],
        'react/no-danger-with-children': [2],
        'react/no-direct-mutation-state': [2],
        'react/no-find-dom-node': [2],
        'react/no-is-mounted': [2],
        'react/no-render-return-value': [2],
        'react/no-string-refs': [2],
        'react/no-unescaped-entities': [2],
        'react/no-unknown-property': [2],
        'react/require-render-return': [2],
        'react/rules-of-hooks': [2],
        'react/exhaustive-deps': [2],
        'react/no-unsafe': [
          'error',
          {
            checkAliases: true,
          },
        ],
      },
    },
    {
      files: ['*.config.{js,mjs,cjs}', 'scripts/**/*.{js,mjs,cjs}'],
      globals: globals.node,
    },
    {
      files: [
        'src/**/*.{test,spec}.{js,jsx}',
        'src/setupTests.js',
        'src/testUtils/**/*.{js,jsx}',
      ],
      globals: { ...globals.browser, ...globals.node },
      rules: {
        'react/jsx-no-undef': 'error',
      },
    },
  ],
};
