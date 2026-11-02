import { getApiUrl } from '../config/api';
import { getErrorMessage, isAbortError } from '../utils/errors';

/**
 * Read the API's user-facing error while preserving request cancellation.
 * @param {Response} response - Fetch response object
 * @returns {Promise<string>} User-friendly error message
 */
async function parseErrorResponse(response) {
  try {
    const data = await response.json();
    if (data.error) {
      return data.detail || data.error;
    }
    return data.message || `Server error (${response.status})`;
  } catch (err) {
    if (isAbortError(err)) {
      throw err;
    }
    return `Server error (${response.status}: ${response.statusText})`;
  }
}

/**
 * @template T
 * @param {string} path
 * @param {{signal?: AbortSignal, notFoundMessage?: string}} [options]
 * @returns {Promise<T>} The response follows the requested API contract.
 */
async function fetchStoryData(path, { signal, notFoundMessage } = {}) {
  try {
    const response = await fetch(getApiUrl(path), { signal });

    if (!response.ok) {
      if (response.status === 404 && notFoundMessage) {
        throw new Error(notFoundMessage);
      }
      const errorMessage = await parseErrorResponse(response);
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (err) {
    if (isAbortError(err) || signal?.aborted) {
      throw err;
    }
    console.error(`[storyApi] Fetch error for ${path}:`, err);

    if (getErrorMessage(err, '').includes('Failed to fetch')) {
      throw new Error(
        'Unable to connect to the server. Please check your internet connection.'
      );
    }
    throw err;
  }
}

/**
 * Fetch the story list. Existing callers can omit the options argument.
 * @param {{signal?: AbortSignal}} options - Optional cancellation signal
 * @returns {Promise<import('../types').StorySummary[]>} Available story summaries
 */
export const getAllStories = ({ signal } = {}) =>
  fetchStoryData('/api/stories/', { signal });

/**
 * Fetch a single story by ID from the API
 * @param {string|number} storyId - Story ID
 * @param {{signal?: AbortSignal}} options - Optional cancellation signal
 * @returns {Promise<import('../types').Story>} Story with its paragraphs and words
 * @throws {Error} With user-friendly error message
 */
export const getStoryById = (storyId, { signal } = {}) =>
  fetchStoryData(`/api/stories/${storyId}/`, {
    signal,
    notFoundMessage:
      'Story not found. It may have been removed or the link is incorrect.',
  });
