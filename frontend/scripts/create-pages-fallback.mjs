import { copyFile } from 'node:fs/promises';
import { URL } from 'node:url';

// Pages serves this document for deep links; React Router keeps the requested URL.
await copyFile(
  new URL('../dist/index.html', import.meta.url),
  new URL('../dist/404.html', import.meta.url)
);
