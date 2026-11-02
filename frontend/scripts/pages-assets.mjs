import { readdir } from 'node:fs/promises';
import { pagesBase, pagesResourceUrl } from './pages-requests.mjs';

export async function listPagesAssets(outputDirectory) {
  const assets = [];

  async function visit(directory, prefix) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const name = encodeURIComponent(entry.name);
      if (entry.isDirectory()) {
        await visit(new URL(`${name}/`, directory), `${prefix}${name}/`);
      } else if (entry.isFile()) {
        assets.push(`${prefix}${name}`);
      }
    }
  }

  await visit(outputDirectory, pagesBase);
  return assets;
}

export function selectPagesAssets(html, buildAssets) {
  const references = [...html.matchAll(/(?:src|href)="([^"]+)"/g)].map(
    ([, resource]) => resource
  );
  for (const resource of references) {
    const url = pagesResourceUrl(resource, 80);
    if (resource !== url.pathname || !buildAssets.includes(resource)) {
      throw new Error('HTML resource is not a file in the Pages build');
    }
  }

  // Request paths come from the build directory. HTML only selects which files
  // to check, and every reference is validated before any request can start.
  return buildAssets.filter((asset) => references.includes(asset));
}
