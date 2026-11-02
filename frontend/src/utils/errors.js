/**
 * Cancellation can come from another browser realm, so instanceof Error alone
 * does not cover every DOMException returned by fetch.
 * @param {unknown} error
 */
export function isAbortError(error) {
  return (
    typeof error === 'object' &&
    error !== null &&
    'name' in error &&
    error.name === 'AbortError'
  );
}

/** @param {unknown} error @param {string} fallback */
export function getErrorMessage(error, fallback) {
  return typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof error.message === 'string'
    ? error.message
    : fallback;
}
