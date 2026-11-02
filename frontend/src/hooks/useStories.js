import { useState, useEffect, useCallback } from 'react';
import { getAllStories } from '../api/storyApi';
import { getErrorMessage } from '../utils/errors';

/* Custom hook to fetch and manage the state for the story list. */
export function useStories() {
  const [stories, setStories] = useState(
    /** @type {import('../types').StorySummary[]} */ ([])
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(/** @type {string|null} */ (null));

  const fetchStories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllStories();
      setStories(data);
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load stories.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStories();
  }, [fetchStories]);

  return { stories, loading, error, refetch: fetchStories };
}
