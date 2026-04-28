/**
 * API Configuration
 * Reads API base URL from environment variable
 * Falls back to relative path for development with proxy
 */

// Get API URL from environment variable or use relative path (for Vite proxy)
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Construct full API URL
 * @param {string} path - API endpoint path (e.g., '/api/stories/')
 * @returns {string} Full API URL
 */
export const getApiUrl = (path) => {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

export default API_BASE_URL;
