import assert from 'node:assert/strict';
import { once } from 'node:events';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname } from 'node:path';
import { test } from 'node:test';
import { URL } from 'node:url';
import {
  fetchPagesResource,
  pagesBase as base,
  pagesResourceUrl,
} from './pages-requests.mjs';

const outputDirectory = new URL('../dist/', import.meta.url);
const indexHtml = await readFile(
  new URL('index.html', outputDirectory),
  'utf8'
);
const fallbackHtml = await readFile(
  new URL('404.html', outputDirectory),
  'utf8'
);
const resources = [...indexHtml.matchAll(/(?:src|href)="([^"]+)"/g)].map(
  ([, url]) => url
);

test('the fallback preserves the application and absolute asset paths', async () => {
  assert.equal(fallbackHtml, indexHtml);
  assert.match(fallbackHtml, /<div id="root"><\/div>/);
  assert.match(fallbackHtml, /<script type="module"/);
  assert.ok(resources.some((resource) => resource.endsWith('.js')));
  assert.ok(resources.some((resource) => resource.endsWith('.css')));

  for (const resource of resources) {
    const pathname = pagesResourceUrl(resource, 80).pathname;
    const file = new URL(pathname.slice(base.length), outputDirectory);
    assert.ok((await readFile(file)).length > 0, `Empty asset: ${resource}`);
  }
});

test('Pages-style 404 responses can load the app without hiding missing assets', async (t) => {
  // A test server models Pages: missing files use 404.html and retain status 404.
  // Vite preview's history fallback would return 200 and mask the original bug.
  const server = createServer(async (request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname;
    const relativePath = pathname.startsWith(base)
      ? pathname.slice(base.length)
      : null;
    try {
      if (relativePath === null) throw new Error('Outside the project path');
      const filename = relativePath || 'index.html';
      const data = await readFile(new URL(filename, outputDirectory));
      const contentTypes = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.ico': 'image/x-icon',
      };
      response.writeHead(200, {
        'Content-Type':
          contentTypes[extname(filename)] || 'application/octet-stream',
      });
      response.end(data);
    } catch {
      response.writeHead(404, { 'Content-Type': 'text/html' });
      response.end(fallbackHtml);
    }
  });
  t.after(() => new Promise((resolve) => server.close(resolve)));
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const port = server.address().port;

  for (const path of ['story/1', 'story/1?from=bookmark']) {
    const response = await fetchPagesResource(base + path, port);
    assert.equal(response.status, 404);
    assert.match(response.headers.get('content-type'), /text\/html/);
    assert.equal(await response.text(), indexHtml);
  }

  for (const resource of resources) {
    const response = await fetchPagesResource(resource, port);
    assert.equal(response.status, 200, resource);
    if (resource.endsWith('.js') || resource.endsWith('.css')) {
      assert.doesNotMatch(response.headers.get('content-type'), /text\/html/);
    }
    assert.ok((await response.arrayBuffer()).byteLength > 0);
  }

  for (const path of ['assets/missing-build.js', 'assets/missing-build.css']) {
    const response = await fetchPagesResource(base + path, port);
    assert.equal(
      response.status,
      404,
      `Missing asset must not report success: ${path}`
    );
    await response.arrayBuffer();
  }
});
