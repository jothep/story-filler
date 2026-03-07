//api/storyApi.js
// Defines asynchronous functions for fetching story data from the API.
// Provides `getAllStories` to fetch the list and `getStoryById` to fetch a single story.

/**
 * Parse error response from API
 * @param {Response} response - Fetch response object
 * @returns {Promise<string>} User-friendly error message
 */
async function parseErrorResponse(response) {
  try {
    const data = await response.json();
    // Check if API returned a structured error
    if (data.error) {
      return data.detail || data.error;
    }
    return data.message || `Server error (${response.status})`;
  } catch {
    // Failed to parse JSON, return generic message
    return `Server error (${response.status}: ${response.statusText})`;
  }
}

/**
 * Fetch all stories from the API
 * @returns {Promise<Array>} Array of story objects
 * @throws {Error} With user-friendly error message
 */
export const getAllStories = async () => {
  const API_URL = '/api/stories/';

  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      const errorMessage = await parseErrorResponse(response);
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data;

  } catch (err) {
    console.error('[storyApi] Fetch Error for all stories:', err);

    // Re-throw with user-friendly message
    if (err.message.includes('Failed to fetch')) {
      throw new Error('Unable to connect to the server. Please check your internet connection.');
    }

    throw err;
  }
};

/**
 * Fetch a single story by ID from the API
 * @param {string|number} storyId - Story ID
 * @returns {Promise<Object>} Story object
 * @throws {Error} With user-friendly error message
 */
export const getStoryById = async (storyId) => {
  const API_URL = `/api/stories/${storyId}/`;

  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      const errorMessage = await parseErrorResponse(response);

      // Special handling for 404
      if (response.status === 404) {
        throw new Error(`Story not found. It may have been removed or the link is incorrect.`);
      }

      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data;

  } catch (err) {
    console.error(`[storyApi] Fetch Error for story ${storyId}:`, err);

    // Re-throw with user-friendly message
    if (err.message.includes('Failed to fetch')) {
      throw new Error('Unable to connect to the server. Please check your internet connection.');
    }

    throw err;
  }
};
