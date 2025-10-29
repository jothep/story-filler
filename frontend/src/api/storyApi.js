//api/storyApi.js
// Defines asynchronous functions for fetching story data from the API.
// Provides `getAllStories` to fetch the list and `getStoryById` to fetch a single story.

export const getAllStories = async () => {
  const API_URL = '/api/stories/';

  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error(`Network response was not ok (status: ${response.status})`);
    }

    const data = await response.json();
    return data; 

  } catch (err) {
    console.error('[storyApi] Fetch Error for all stories:', err);
    throw err;
  }
};

export const getStoryById = async (storyId) => {
  const API_URL = `/api/stories/${storyId}/`;

  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error(`Network response was not ok (status: ${response.status})`);
    }

    const data = await response.json();
    return data;

  } catch (err) {
    console.error(`[storyApi] Fetch Error for story ${storyId}:`, err);
    throw err; 
  }
};
