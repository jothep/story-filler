export const pagesBase = '/story-filler/';

export function pagesResourceUrl(resource, port) {
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('Expected a local test server port');
  }
  if (
    typeof resource !== 'string' ||
    !resource.startsWith(pagesBase) ||
    /[\s\\]|\p{Cc}/u.test(resource)
  ) {
    throw new Error('Expected an absolute Pages project path');
  }

  // Reject traversal and encoded separators before URL normalization or file IO.
  for (const segment of resource.split(/[?#]/, 1)[0].split('/')) {
    const decoded = decodeURIComponent(segment);
    if (
      decoded === '.' ||
      decoded === '..' ||
      /[/\\\s]|\p{Cc}/u.test(decoded)
    ) {
      throw new Error('Invalid Pages project path segment');
    }
  }

  const origin = new URL(`http://127.0.0.1:${port}`).origin;
  const url = new URL(resource, origin);
  if (
    url.origin !== origin ||
    !url.pathname.startsWith(pagesBase) ||
    url.username ||
    url.password ||
    url.hash
  ) {
    throw new Error('Expected a resource on the local Pages test server');
  }
  return url;
}

export async function fetchPagesResource(resource, port) {
  // Generated HTML may supply only the path. The destination is always loopback,
  // and even a redirect to another local port must not be followed.
  return globalThis.fetch(pagesResourceUrl(resource, port), {
    redirect: 'error',
  });
}
