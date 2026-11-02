import assert from 'node:assert/strict';
import { once } from 'node:events';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';
import { fetchPagesResource } from './pages-requests.mjs';
import { listPagesAssets, selectPagesAssets } from './pages-assets.mjs';

async function localServer(t, handler) {
  const server = createServer(handler);
  t.after(() => new Promise((resolve) => server.close(resolve)));
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  return server.address().port;
}

test('HTML must match the build inventory before any asset request is sent', async (t) => {
  const directory = await mkdtemp(join(tmpdir(), 'pages-assets-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  await mkdir(join(directory, 'assets'));
  await writeFile(
    join(directory, 'assets', 'app.js'),
    'console.log("fixture");'
  );
  await writeFile(
    join(directory, 'assets', 'app.css'),
    'body { color: black; }'
  );
  const inventory = await listPagesAssets(pathToFileURL(`${directory}/`));
  assert.deepEqual(inventory.sort(), [
    '/story-filler/assets/app.css',
    '/story-filler/assets/app.js',
  ]);
  const validHtml = '<script src="/story-filler/assets/app.js"></script>';
  assert.deepEqual(selectPagesAssets(validHtml, inventory), [
    '/story-filler/assets/app.js',
  ]);

  let requests = 0;
  const port = await localServer(t, (_request, response) => {
    requests += 1;
    response.end('must not be requested');
  });
  for (const resource of [
    '/story-filler/assets/unlisted.js',
    '/story-filler/assets/app.js?file-content=must-not-leave',
    '/story-filler/../private.txt',
    '//example.invalid/leak',
    '@example.invalid/leak',
  ]) {
    await assert.rejects(async () => {
      const assets = selectPagesAssets(
        `${validHtml}<link href="${resource}">`,
        inventory
      );
      for (const asset of assets) {
        await fetchPagesResource(asset, port);
      }
    });
  }
  assert.equal(requests, 0);
});

test('Pages requests reach only the specified loopback server and preserve queries', async (t) => {
  const requests = [];
  const port = await localServer(t, (request, response) => {
    requests.push({ host: request.headers.host, path: request.url });
    response.end('local asset');
  });
  for (const path of [
    '/story-filler/assets/index-Abc123.js',
    '/story-filler/story/1?from=bookmark',
  ]) {
    const response = await fetchPagesResource(path, port);
    assert.equal(await response.text(), 'local asset');
    assert.deepEqual(requests.at(-1), {
      host: `127.0.0.1:${port}`,
      path,
    });
  }
  assert.equal(requests.length, 2);
});

test('malformed, external, credential-bearing, and escaping paths make no request', async (t) => {
  let requests = 0;
  const port = await localServer(t, (_request, response) => {
    requests += 1;
    response.end('must not be requested');
  });
  for (const path of [
    'https://example.invalid/asset.js',
    `http://127.0.0.1:${port}/story-filler/asset.js`,
    '@example.invalid/asset.js',
    `@127.0.0.1:${port}/story-filler/asset.js`,
    '//example.invalid/asset.js',
    `//user:password@127.0.0.1:${port}/story-filler/asset.js`,
    `http://127.0.0.1:${port}@example.invalid/asset.js`,
    '/\\example.invalid/asset.js',
    '/story-filler/\\example.invalid/asset.js',
    '/story-filler/../outside.js',
    '/story-filler/assets/../../outside.js',
    '/story-filler/%2e%2e/outside.js',
    '/story-filler/assets/%2E%2E/index.js',
    '/story-filler/%2f%2fexample.invalid/asset.js',
    '/story-filler/%5c%5cexample.invalid/asset.js',
    '/story-filler/%00asset.js',
    '/story-filler/asset.js\r\nHost: example.invalid',
    '/story-filler/asset.js\t',
    '/story-filler/%zz.js',
    '/story-filler/asset.js#fragment',
    '/different-project/asset.js',
    'assets/index.js',
    '',
    null,
  ]) {
    await assert.rejects(
      fetchPagesResource(path, port),
      undefined,
      String(path)
    );
  }
  for (const invalidPort of [0, -1, 65536, 1.5, '80', NaN]) {
    await assert.rejects(
      fetchPagesResource('/story-filler/asset.js', invalidPort)
    );
  }
  assert.equal(requests, 0);
});

test('redirects cannot send Pages requests to another origin or path', async (t) => {
  let destinationRequests = 0;
  const destinationPort = await localServer(t, (_request, response) => {
    destinationRequests += 1;
    response.end('must not be requested');
  });
  let redirectRequests = 0;
  const locations = [
    `http://127.0.0.1:${destinationPort}/leak`,
    `//127.0.0.1:${destinationPort}/leak`,
    `http://user:password@127.0.0.1:${destinationPort}/leak`,
    '/outside-project',
    '/story-filler/another-asset.js',
  ];
  const port = await localServer(t, (request, response) => {
    const index = Number(
      new URL(request.url, 'http://127.0.0.1').searchParams.get('case')
    );
    redirectRequests += 1;
    response.writeHead(302, { Location: locations[index] });
    response.end();
  });
  for (let index = 0; index < locations.length; index += 1) {
    await assert.rejects(
      fetchPagesResource(`/story-filler/redirect?case=${index}`, port)
    );
  }
  assert.equal(redirectRequests, locations.length);
  assert.equal(destinationRequests, 0);
});
