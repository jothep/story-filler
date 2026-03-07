// Custom hook to fetch and manage the state for the list of all stories.
import { useState, useEffect, useCallback } from 'react';
import { getAllStories } from '../api/storyApi';

/* Custom hook to fetch and manage the state for the story list. */
export function useStories() {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllStories();
      setStories(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStories();
  }, [fetchStories]);

  return { stories, loading, error, refetch: fetchStories };
}
