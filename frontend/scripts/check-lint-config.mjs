import assert from 'node:assert/strict';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { ESLint } from 'eslint';

const eslint = new ESLint({
  cwd: fileURLToPath(new URL('../', import.meta.url)),
});

const invalidExamples = [
  {
    name: 'missing React list keys',
    rule: 'react/jsx-key',
    code: `export default function List() {
      return <ul>{['one', 'two'].map(label => <li>{label}</li>)}</ul>;
    }`,
  },
  {
    name: 'duplicate JSX properties',
    rule: 'react/jsx-no-duplicate-props',
    code: `export default function Button() {
      return <button type="button" type="submit">Save</button>;
    }`,
  },
  {
    name: 'undefined JSX components',
    rule: 'react/jsx-no-undef',
    code: 'export default function View() { return <UnknownComponent />; }',
  },
  {
    name: 'unknown DOM properties',
    rule: 'react/no-unknown-property',
    code: 'export default function View() { return <div class="notice" />; }',
  },
  {
    name: 'missing component prop declarations',
    rule: 'react/prop-types',
    code: 'export default function Greeting({ name }) { return <p>{name}</p>; }',
  },
  {
    name: 'class render methods with no return',
    rule: 'react/require-render-return',
    code: `import { Component } from 'react';
      export default class View extends Component {
        render() { document.title = 'Missing result'; }
      }`,
  },
  {
    name: 'HTML injection combined with children',
    rule: 'react/no-danger-with-children',
    code: `export default function View() {
      return <div dangerouslySetInnerHTML={{ __html: 'content' }}>Child</div>;
    }`,
  },
  {
    name: 'conditional Hooks',
    rule: 'react-hooks/rules-of-hooks',
    code: `import { useState } from 'react';
      export default function View() {
        if (document.hidden) useState(0);
        return null;
      }`,
  },
  {
    name: 'missing effect dependencies',
    rule: 'react-hooks/exhaustive-deps',
    code: `import { useEffect, useState } from 'react';
      export default function Counter() {
        const [count] = useState(0);
        useEffect(() => { document.title = String(count); }, []);
        return <span>{count}</span>;
      }`,
  },
  {
    name: 'Node globals in browser code',
    rule: 'no-undef',
    code: 'export const currentDirectory = process.cwd();',
  },
  {
    name: 'browser globals in Node scripts',
    file: 'scripts/lint-example.mjs',
    rule: 'no-undef',
    code: 'export const title = document.title;',
  },
  {
    name: 'undefined names inside component tests',
    file: 'src/lint-example.test.jsx',
    rule: 'no-undef',
    code: `import { expect, test } from 'vitest';
      test('value', () => { expect(missingValue).toBe(1); });`,
  },
];

for (const example of invalidExamples) {
  test(`lint catches ${example.name}`, async () => {
    const [result] = await eslint.lintText(example.code, {
      filePath: example.file || 'src/lint-example.jsx',
    });
    assert.equal(result.fatalErrorCount, 0, JSON.stringify(result.messages));
    assert.ok(
      result.messages.some(
        ({ ruleId, severity }) => ruleId === example.rule && severity === 2
      ),
      `Expected ${example.rule}: ${JSON.stringify(result.messages)}`
    );
  });
}

const validExamples = [
  {
    name: 'a browser component with complete effect dependencies',
    file: 'src/lint-example.jsx',
    code: `import { useEffect, useState } from 'react';
      export default function Counter() {
        const [count] = useState(0);
        useEffect(() => { document.title = String(count); }, [count]);
        return <button type="button">{count}</button>;
      }`,
  },
  {
    name: 'a Node script',
    file: 'scripts/lint-example.mjs',
    code: 'export const currentDirectory = process.cwd();',
  },
  {
    name: 'a Node configuration file',
    file: 'example.config.js',
    code: 'export default { directory: process.cwd() };',
  },
  {
    name: 'a JSX test with explicit Vitest imports',
    file: 'src/lint-example.test.jsx',
    code: `import { render } from '@testing-library/react';
      import { expect, test } from 'vitest';
      test('button', () => {
        render(<button>Go</button>);
        expect(document.body.textContent).toContain('Go');
      });`,
  },
];

for (const example of validExamples) {
  test(`lint accepts ${example.name}`, async () => {
    const [result] = await eslint.lintText(example.code, {
      filePath: example.file,
    });
    assert.deepEqual(result.messages, []);
  });
}
