// eslint.config.js
import globals from 'globals';
import pluginJs from '@eslint/js';
import pluginReactConfig from 'eslint-plugin-react/configs/recommended.js';
import pluginReactJsxRuntime from 'eslint-plugin-react/configs/jsx-runtime.js';

export default [
  pluginJs.configs.recommended,

  pluginReactConfig,

  pluginReactJsxRuntime,

  {
    files: ['src/**/*.{js,jsx}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },

  {
    ignores: [
      'dist/',
      'node_modules/',
      'eslint.config.js',
      'vite.config.js',
      'src/setupTests.js',
      'src/**/*.test.jsx',
      'src/**/*.spec.jsx',
    ],
  },
];
