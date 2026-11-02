// Each pair preserves one reviewed baseline check, including its accepted case.

export const ruleExamples = [
  {
    rule: 'constructor-super',
    invalid: 'export class Child extends Object { constructor() {} }',
    valid: 'export class Child extends Object { constructor() { super(); } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'for-direction',
    invalid:
      'export function run() { for (let i = 0; i < 10; i--) { console.log(i); } }',
    valid:
      'export function run() { for (let i = 0; i < 10; i++) { console.log(i); } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'getter-return',
    invalid: 'export const item = { get value() { console.log("read"); } };',
    valid: 'export const item = { get value() { return 1; } };',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-async-promise-executor',
    invalid:
      'export const task = new Promise(async resolve => { resolve(1); });',
    valid: 'export const task = new Promise(resolve => { resolve(1); });',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-case-declarations',
    invalid:
      'export function run(value) { switch (value) { case 1: const result = 2; return result; default: return 0; } }',
    valid:
      'export function run(value) { switch (value) { case 1: { const result = 2; return result; } default: return 0; } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-class-assign',
    invalid: 'export class Example {} Example = 1;',
    valid: 'export class Example {}',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-compare-neg-zero',
    invalid: 'export function test(value) { return value === -0; }',
    valid: 'export function test(value) { return Object.is(value, -0); }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-cond-assign',
    invalid:
      'export function run(value) { if (value = 1) return value; return 0; }',
    valid:
      'export function run(value) { if (value === 1) return value; return 0; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-const-assign',
    invalid: 'export const value = 1; value = 2;',
    valid: 'export let value = 1; value = 2;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-constant-binary-expression',
    invalid: 'export const value = [] || null;',
    valid: 'export const value = Math.random() || null;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-constant-condition',
    invalid:
      'export function run() { while (false) { console.log("never"); } }',
    valid: 'export function run(value) { while (value) { break; } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-control-regex',
    invalid: 'export const pattern = /\\x00/;',
    valid: 'export const pattern = /a/;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-debugger',
    invalid: 'export function run() { debugger; }',
    valid: 'export function run() { return 1; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-delete-var',
    invalid: 'export function run(value) { delete value; }',
    valid: 'export function run(value) { delete value.field; }',
    file: 'src/lint-example.js',
    parserMessage: 'Delete of an unqualified identifier in strict mode.',
  },
  {
    rule: 'no-dupe-args',
    invalid: 'export function run(value, value) { return value; }',
    valid: 'export function run(first, second) { return first + second; }',
    file: 'src/lint-example.js',
    parserMessage: 'Identifier `value` has already been declared',
  },
  {
    rule: 'no-dupe-class-members',
    invalid: 'export class Example { run() {} run() {} }',
    valid: 'export class Example { run() {} stop() {} }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-dupe-else-if',
    invalid:
      'export function run(value) { if (value) return 1; else if (value) return 2; return 0; }',
    valid:
      'export function run(value) { if (value === 1) return 1; else if (value === 2) return 2; return 0; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-dupe-keys',
    invalid: 'export const value = { field: 1, field: 2 };',
    valid: 'export const value = { first: 1, second: 2 };',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-duplicate-case',
    invalid:
      'export function run(value) { switch (value) { case 1: return 1; case 1: return 2; default: return 0; } }',
    valid:
      'export function run(value) { switch (value) { case 1: return 1; case 2: return 2; default: return 0; } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-empty',
    invalid: 'export function run(value) { if (value) {} }',
    valid:
      'export function run(value) { if (value) { /* intentionally empty */ } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-empty-character-class',
    invalid: 'export const pattern = /[]/;',
    valid: 'export const pattern = /[a]/;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-empty-pattern',
    invalid: 'export const {} = {};',
    valid: 'export const { value } = { value: 1 };',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-empty-static-block',
    invalid: 'export class Example { static {} }',
    valid:
      'export class Example { static { /* reserved for initialization */ } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-ex-assign',
    invalid:
      'export function run() { try { JSON.parse("{}"); } catch (error) { error = null; console.log(error); } }',
    valid:
      'export function run() { try { JSON.parse("{}"); } catch (error) { console.log(error); } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-extra-boolean-cast',
    invalid: 'export function run(value) { if (!!value) return 1; return 0; }',
    valid: 'export function run(value) { if (value) return 1; return 0; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-fallthrough',
    invalid:
      'export function run(value) { switch (value) { case 1: console.log(value); case 2: return 2; default: return 0; } }',
    valid:
      'export function run(value) { switch (value) { case 1: console.log(value); break; case 2: return 2; default: return 0; } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-func-assign',
    invalid: 'export function run() {} run = 1;',
    valid: 'export function run() {}',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-global-assign',
    invalid: 'Object = null;',
    valid: 'export const savedObject = Object;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-import-assign',
    invalid: 'import { value } from "module"; value = 1;',
    valid: 'import { value } from "module"; export const copy = value;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-invalid-regexp',
    invalid: 'export const pattern = new RegExp("[");',
    valid: 'export const pattern = new RegExp("[a]");',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-irregular-whitespace',
    invalid: 'export const value = 1;',
    valid: 'export const value = " ";',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-loss-of-precision',
    invalid: 'export const value = 9007199254740993;',
    valid: 'export const value = 9007199254740993n;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-misleading-character-class',
    invalid: 'export const pattern = /[😀]/;',
    valid: 'export const pattern = /[😀]/u;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-new-native-nonconstructor',
    invalid: 'export const value = new Symbol("key");',
    valid: 'export const value = Symbol("key");',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-nonoctal-decimal-escape',
    invalid: 'export const value = "\\8";',
    valid: 'export const value = "8";',
    file: 'src/lint-example.js',
    parserMessage: 'Invalid escape sequence',
  },
  {
    rule: 'no-obj-calls',
    invalid: 'export const value = Math();',
    valid: 'export const value = Math.random();',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-octal',
    invalid: 'export const value = 071;',
    valid: 'export const value = 0o71;',
    file: 'src/lint-example.js',
    parserMessage:
      "'0'-prefixed octal literals and octal escape sequences are deprecated",
  },
  {
    rule: 'no-prototype-builtins',
    invalid:
      'export function check(value) { return value.hasOwnProperty("key"); }',
    valid:
      'export function check(value) { return Object.prototype.hasOwnProperty.call(value, "key"); }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-redeclare',
    invalid:
      'export function run() { var value = 1; var value = 2; return value; }',
    valid: 'export function run() { let value = 1; value = 2; return value; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-regex-spaces',
    invalid: 'export const pattern = /a  b/;',
    valid: 'export const pattern = /a {2}b/;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-self-assign',
    invalid: 'export function run(value) { value = value; return value; }',
    valid: 'export function run(value) { return value; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-setter-return',
    invalid:
      'export const item = { set value(input) { console.log(input); return 1; } };',
    valid: 'export const item = { set value(input) { console.log(input); } };',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-shadow-restricted-names',
    invalid: 'export function run(undefined) { return undefined; }',
    valid: 'export function run(value) { return value; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-sparse-arrays',
    invalid: 'export const values = [1,,3];',
    valid: 'export const values = [1,undefined,3];',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-this-before-super',
    invalid:
      'export class Child extends Object { constructor() { this.value = 1; super(); } }',
    valid:
      'export class Child extends Object { constructor() { super(); this.value = 1; } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-undef',
    invalid: 'export const value = missingValue;',
    valid: 'export const value = document.title;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-unexpected-multiline',
    invalid: 'export const value = document.title\n[1,2].forEach(console.log);',
    valid: 'export const value = document.title;\n[1,2].forEach(console.log);',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-unreachable',
    invalid: 'export function run() { return 1; console.log("never"); }',
    valid: 'export function run() { console.log("now"); return 1; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-unsafe-finally',
    invalid:
      'export function run() { try { return 1; } finally { return 2; } }',
    valid:
      'export function run() { try { return 1; } finally { console.log("done"); } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-unsafe-negation',
    invalid: 'export function check(value) { return !value in {}; }',
    valid: 'export function check(value) { return !(value in {}); }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-unsafe-optional-chaining',
    invalid: 'export function run(value) { return (value?.call)(); }',
    valid: 'export function run(value) { return value?.call(); }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-unused-labels',
    invalid: 'export function run() { unused: console.log("value"); }',
    valid:
      'export function run() { used: { console.log("value"); break used; } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-unused-private-class-members',
    invalid: 'export class Example { #value = 1; }',
    valid:
      'export class Example { #value = 1; get value() { return this.#value; } }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-unused-vars',
    invalid: 'const unused = 1; export const value = 2;',
    valid: 'const used = 1; export const value = used;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-useless-backreference',
    invalid: 'export const pattern = /\\1(a)/;',
    valid: 'export const pattern = /(a)\\1/;',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-useless-catch',
    invalid:
      'export function run() { try { JSON.parse("{}"); } catch (error) { throw error; } }',
    valid: 'export function run() { return JSON.parse("{}"); }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-useless-escape',
    invalid: 'export const value = "\\a";',
    valid: 'export const value = "\\n";',
    file: 'src/lint-example.js',
  },
  {
    rule: 'no-with',
    invalid: 'with (document) { title = "bad"; }',
    valid: 'document.title = "good";',
    file: 'src/lint-example.js',
  },
  {
    rule: 'require-yield',
    invalid: 'export function* values() { return 1; }',
    valid: 'export function* values() { yield 1; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'use-isnan',
    invalid: 'export function check(value) { return value === NaN; }',
    valid: 'export function check(value) { return Number.isNaN(value); }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'valid-typeof',
    invalid:
      'export function check(value) { return typeof value === "strnig"; }',
    valid: 'export function check(value) { return typeof value === "string"; }',
    file: 'src/lint-example.js',
  },
  {
    rule: 'react/display-name',
    invalid: 'import {memo} from "react"; export default memo(() => <div />);',
    valid:
      'import {memo} from "react"; export default memo(function View() { return <div />; });',
    file: 'src/lint-example.jsx',
    engine: 'typescript',
    diagnosticCode: 95001,
  },
  {
    rule: 'react/jsx-key',
    invalid:
      'export default function View() { return <ul>{[1,2].map(value => <li>{value}</li>)}</ul>; }',
    valid:
      'export default function View() { return <ul>{[1,2].map(value => <li key={value}>{value}</li>)}</ul>; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/jsx-no-comment-textnodes',
    invalid: 'export default function View() { return <div>// comment</div>; }',
    valid:
      'export default function View() { return <div>{/* comment */}</div>; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/jsx-no-duplicate-props',
    invalid:
      'export default function View() { return <button type="button" type="submit" />; }',
    valid:
      'export default function View() { return <button type="button" />; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/jsx-no-target-blank',
    invalid:
      'export default function View() { return <a href="https://example.com" target="_blank">Go</a>; }',
    valid:
      'export default function View() { return <a href="https://example.com" target="_blank" rel="noopener noreferrer">Go</a>; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/jsx-no-undef',
    invalid: 'export default function View() { return <Missing />; }',
    valid:
      'function Present() { return <p />; } export default function View() { return <Present />; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/jsx-uses-vars',
    invalid:
      'function Present() { return <p />; } export default function View() { return <p />; }',
    valid:
      'function Present() { return <p />; } export default function View() { return <Present />; }',
    file: 'src/lint-example.jsx',
    expectedRule: 'no-unused-vars',
  },
  {
    rule: 'react/no-children-prop',
    invalid:
      'export default function View() { return <div children="text" />; }',
    valid: 'export default function View() { return <div>text</div>; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/no-danger-with-children',
    invalid:
      'export default function View() { return <div dangerouslySetInnerHTML={{__html:"text"}}>child</div>; }',
    valid:
      'export default function View() { return <div dangerouslySetInnerHTML={{__html:"text"}} />; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/no-deprecated',
    invalid:
      'import React from "react"; export const value = React.createClass({render() { return <div />; }});',
    valid:
      'import {createElement} from "react"; export const value = createElement("div");',
    file: 'src/lint-example.jsx',
    engine: 'typescript',
    diagnosticCode: 2339,
  },
  {
    rule: 'react/no-direct-mutation-state',
    invalid:
      'import {Component} from "react"; export default class View extends Component { state = {value:0}; update() {this.state.value = 1;} render() {return <p />;} }',
    valid:
      'import {Component} from "react"; export default class View extends Component { state = {value:0}; update() {this.setState({value:1});} render() {return <p />;} }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/no-find-dom-node',
    invalid:
      'import ReactDOM from "react-dom"; export const value = ReactDOM.findDOMNode(document.body);',
    valid: 'export const value = document.body;',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/no-is-mounted',
    invalid:
      'import {Component} from "react"; export default class View extends Component { check() {return this.isMounted();} render() {return <p />;} }',
    valid:
      'import {Component} from "react"; export default class View extends Component { render() {return <p />;} }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/no-render-return-value',
    invalid:
      'import ReactDOM from "react-dom"; export const value = ReactDOM.render(<p />, document.body);',
    valid:
      'import {createRoot} from "react-dom/client"; createRoot(document.body).render(<p />);',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/no-string-refs',
    invalid:
      'import {Component} from "react"; export default class View extends Component { render() {return <input ref="input" />;} }',
    valid:
      'import {Component, createRef} from "react"; export default class View extends Component { input = createRef(); render() {return <input ref={this.input} />;} }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/no-unescaped-entities',
    invalid: "export default function View() { return <p>Don't</p>; }",
    valid: 'export default function View() { return <p>Don&apos;t</p>; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/no-unknown-property',
    invalid: 'export default function View() { return <div class="value" />; }',
    valid:
      'export default function View() { return <div className="value" />; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react/prop-types',
    invalid: 'export default function View({value}) { return <p>{value}</p>; }',
    valid:
      '/** @param {{value?: string}} props */\nexport default function View({value}) { return <p>{value}</p>; }',
    file: 'src/lint-example.jsx',
    engine: 'typescript',
    diagnosticCode: 7031,
  },
  {
    rule: 'react/require-render-return',
    invalid:
      'import {Component} from "react"; export default class View extends Component { render() {document.title = "value";} }',
    valid:
      'import {Component} from "react"; export default class View extends Component { render() {return <p />;} }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react-hooks/rules-of-hooks',
    invalid:
      'import {useState} from "react"; export default function View() { if (document.hidden) useState(0); return null; }',
    valid:
      'import {useState} from "react"; export default function View() { const [value] = useState(0); return <p>{value}</p>; }',
    file: 'src/lint-example.jsx',
  },
  {
    rule: 'react-hooks/exhaustive-deps',
    invalid:
      'import {useState,useEffect} from "react"; export default function View() { const [value] = useState(0); useEffect(() => {document.title=String(value)}, []); return <p>{value}</p>; }',
    valid:
      'import {useState,useEffect} from "react"; export default function View() { const [value] = useState(0); useEffect(() => {document.title=String(value)}, [value]); return <p>{value}</p>; }',
    file: 'src/lint-example.jsx',
  },
];

export const scopeExamples = [
  {
    name: 'browser supports DOM',
    file: 'src/scope.js',
    code: 'export const value = document.title;',
    expectedRule: null,
  },
  {
    name: 'browser rejects process',
    file: 'src/scope.js',
    code: 'export const value = process.cwd();',
    expectedRule: 'no-undef',
  },
  {
    name: 'browser rejects Buffer',
    file: 'src/scope.js',
    code: 'export const value = Buffer.from("data");',
    expectedRule: 'no-undef',
  },
  {
    name: 'browser rejects require',
    file: 'src/scope.js',
    code: 'export const value = require("node:path");',
    expectedRule: 'no-undef',
  },
  {
    name: 'browser rejects module',
    file: 'src/scope.js',
    code: 'module.exports = {};',
    expectedRule: 'no-undef',
  },
  {
    name: 'node config supports process',
    file: 'example.config.js',
    code: 'export default {directory:process.cwd()};',
    expectedRule: null,
  },
  {
    name: 'node mjs config supports process',
    file: 'example.config.mjs',
    code: 'export default {directory:process.cwd()};',
    expectedRule: null,
  },
  {
    name: 'node cjs config supports require',
    file: 'example.config.cjs',
    code: 'module.exports = require("node:path");',
    expectedRule: null,
  },
  {
    name: 'node scripts support process',
    file: 'scripts/nested/scope.mjs',
    code: 'export const value = process.cwd();',
    expectedRule: null,
  },
  {
    name: 'node scripts reject document',
    file: 'scripts/nested/scope.mjs',
    code: 'export const value = document.title;',
    expectedRule: 'no-undef',
  },
  {
    name: 'node config rejects window',
    file: 'example.config.js',
    code: 'export default window.location;',
    expectedRule: 'no-undef',
  },
  {
    name: 'tests support browser and Node',
    file: 'src/scope.test.jsx',
    code: 'export const value = [document.title, process.cwd()];',
    expectedRule: null,
  },
  {
    name: 'spec files support browser and Node',
    file: 'src/scope.spec.jsx',
    code: 'export const value = [document.title, process.cwd()];',
    expectedRule: null,
  },
  {
    name: 'setup supports browser and Node',
    file: 'src/setupTests.js',
    code: 'export const value = [document.title, process.cwd()];',
    expectedRule: null,
  },
  {
    name: 'helpers support browser and Node',
    file: 'src/testUtils/nested/helper.jsx',
    code: 'export const value = [document.title, process.cwd()];',
    expectedRule: null,
  },
  {
    name: 'test declarations require imports',
    file: 'src/scope.test.js',
    code: 'test("example", () => {});',
    expectedRule: 'no-undef',
  },
  {
    name: 'test assertions require imports',
    file: 'src/scope.test.js',
    code: 'expect(true).toBe(true);',
    expectedRule: 'no-undef',
  },
  {
    name: 'test mocks require imports',
    file: 'src/scope.test.js',
    code: 'export const mock = vi.fn();',
    expectedRule: 'no-undef',
  },
  {
    name: 'test imports accepted',
    file: 'src/scope.test.js',
    code: 'import {test, expect, vi} from "vitest"; test("example", () => {expect(vi.fn()).toBeTruthy();});',
    expectedRule: null,
  },
  {
    name: 'test fixtures omit prop declarations',
    file: 'src/scope.test.jsx',
    code: 'export default function View({value}) {return <p>{value}</p>;}',
    expectedRule: null,
  },
  {
    name: 'shared fixtures omit prop declarations',
    file: 'src/testUtils/helper.jsx',
    code: 'export default function View({value}) {return <p>{value}</p>;}',
    expectedRule: null,
  },
  {
    name: 'tests still reject missing JSX names',
    file: 'src/scope.test.jsx',
    code: 'export default function View() {return <Missing />;}',
    expectedRule: 'react/jsx-no-undef',
  },
  {
    name: 'tests track JSX component usage',
    file: 'src/scope.test.jsx',
    code: 'function Child() {return <p />;} export default function View() {return <Child />;}',
    expectedRule: null,
  },
  {
    name: 'other root files have no Node globals',
    file: 'other.mjs',
    code: 'export const value = process.cwd();',
    expectedRule: 'no-undef',
  },
  {
    name: 'src mjs does not inherit JS browser scope',
    file: 'src/other.mjs',
    code: 'export const value = document.title;',
    expectedRule: 'no-undef',
  },
  {
    name: 'nonmatching config name has no Node globals',
    file: 'other.config.extra.js',
    code: 'export const value = process.cwd();',
    expectedRule: 'no-undef',
  },
];

export const optionExamples = [
  {
    name: 'parenthesized assignment permitted',
    file: 'src/options.js',
    code: 'export function run(value) {if ((value = Math.random())) return value; return 0;}',
    expectedRule: null,
  },
  {
    name: 'while true loop permitted',
    file: 'src/options.js',
    code: 'export function run() {while (true) {console.log("work");}}',
    expectedRule: null,
  },
  {
    name: 'other constant loops rejected',
    file: 'src/options.js',
    code: 'export function run() {while (1) {console.log("work");}}',
    expectedRule: 'no-constant-condition',
  },
  {
    name: 'implicit getter return rejected',
    file: 'src/options.js',
    code: 'export const item = {get value() {return;}};',
    expectedRule: 'getter-return',
  },
  {
    name: 'empty catch rejected',
    file: 'src/options.js',
    code: 'export function run() {try {JSON.parse("{}");} catch {}}',
    expectedRule: 'no-empty',
  },
  {
    name: 'empty parameter destructuring rejected',
    file: 'src/options.js',
    code: 'export function run({}) {return 1;}',
    expectedRule: 'no-empty-pattern',
  },
  {
    name: 'irregular comment whitespace rejected',
    file: 'src/options.js',
    code: 'export const value = 1; // note',
    expectedRule: 'no-irregular-whitespace',
  },
  {
    name: 'irregular template whitespace rejected',
    file: 'src/options.js',
    code: 'export const value = ` `;',
    expectedRule: 'no-irregular-whitespace',
  },
  {
    name: 'property self assignment rejected',
    file: 'src/options.js',
    code: 'export function run(value) {value.field = value.field;}',
    expectedRule: 'no-self-assign',
  },
  {
    name: 'globalThis parameter allowed',
    file: 'src/options.js',
    code: 'export function run(globalThis) {return globalThis;}',
    expectedRule: null,
  },
  {
    name: 'typeof unresolved name allowed',
    file: 'src/options.js',
    code: 'export const value = typeof missingValue;',
    expectedRule: null,
  },
  {
    name: 'negated ordering retains old allowance',
    file: 'src/options.js',
    code: 'export function run(value) {return !value < 1;}',
    expectedRule: null,
  },
  {
    name: 'optional arithmetic retains old allowance',
    file: 'src/options.js',
    code: 'export function run(value) {return value?.count + 1;}',
    expectedRule: null,
  },
  {
    name: 'unused leading parameters allowed',
    file: 'src/options.js',
    code: 'export function run(unused, used) {return used;}',
    expectedRule: null,
  },
  {
    name: 'unused caught errors rejected',
    file: 'src/options.js',
    code: 'export function run() {try {return JSON.parse("{}");} catch (error) {return null;}}',
    expectedRule: 'no-unused-vars',
  },
  {
    name: 'typeof comparison variable allowed',
    file: 'src/options.js',
    code: 'export function run(value, expected) {return typeof value === expected;}',
    expectedRule: null,
  },
  {
    name: 'NaN switch case rejected',
    file: 'src/options.js',
    code: 'export function run(value) {switch(value) {case NaN: return 1; default: return 0;}}',
    expectedRule: 'use-isnan',
  },
  {
    name: 'NaN indexOf retains old allowance',
    file: 'src/options.js',
    code: 'export function run(values) {return values.indexOf(NaN);}',
    expectedRule: null,
  },
];

export const componentNameExamples = [
  {
    name: 'anonymous memo',
    code: 'import {memo} from "react"; export default memo(() => <p/>);',
    invalid: true,
  },
  {
    name: 'named memo function',
    code: 'import {memo} from "react"; export default memo(function View(){return <p/>;});',
    invalid: false,
  },
  {
    name: 'anonymous forwardRef',
    code: 'import {forwardRef} from "react"; export default forwardRef(() => <p/>);',
    invalid: true,
  },
  {
    name: 'named forwardRef function',
    code: 'import {forwardRef} from "react"; export default forwardRef(function View(){return <p/>;});',
    invalid: false,
  },
  {
    name: 'aliased memo import',
    code: 'import {memo as wrap} from "react"; export default wrap(() => <p/>);',
    invalid: true,
  },
  {
    name: 'namespace React API',
    code: 'import * as React from "react"; export default React.memo(() => <p/>);',
    invalid: true,
  },
  {
    name: 'explicit displayName',
    code: 'import {memo} from "react"; const View=memo(() => <p/>); View.displayName="View"; export default View;',
    invalid: false,
  },
  {
    name: 'computed displayName',
    code: 'import {memo} from "react"; const View=memo(() => <p/>); View["displayName"]="View"; export default View;',
    invalid: false,
  },
  {
    name: 'unrelated displayName',
    code: 'import {memo} from "react"; const Other=memo(function Other(){return <p/>;}); Other.displayName="Other"; export default memo(() => <p/>);',
    invalid: true,
  },
  {
    name: 'local function named memo',
    code: '/** @param {() => import("react").ReactNode} render */\nfunction memo(render){return render;} export default memo(() => <p/>);',
    invalid: false,
  },
  {
    name: 'local namespace named React',
    code: 'const React={\n/** @param {() => import("react").ReactNode} render */\nmemo(render){return render;}}; export default React.memo(() => <p/>);',
    invalid: false,
  },
  {
    name: 'named callback identifier',
    code: 'import {memo} from "react"; function View(){return <p/>;} export default memo(View);',
    invalid: false,
  },
  {
    name: 'nested wrappers with displayName',
    code: 'import {memo,forwardRef} from "react"; const View=memo(forwardRef(() => <p/>)); View.displayName="View"; export default View;',
    invalid: false,
  },
];
