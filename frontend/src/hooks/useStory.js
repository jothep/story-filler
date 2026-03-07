// Custom hook to fetch and manage the state for a single story by its ID.
import { useState, useEffect, useCallback } from 'react';
import { getStoryById } from '../api/storyApi';

 /* Custom hook to fetch and manage the state for a single story. */
export function useStory(storyId) {
  const [story, setStory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStory = useCallback(async () => {
    if (!storyId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await getStoryById(storyId);
      setStory(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [storyId]);

  useEffect(() => {
    fetchStory();
  }, [fetchStory]);

  return { story, loading, error, refetch: fetchStory };
}
