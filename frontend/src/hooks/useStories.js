// Custom hook to fetch and manage the state for the list of all stories.
import { useState, useEffect } from 'react';
import { getAllStories } from '../api/storyApi';

/* Custom hook to fetch and manage the state for the story list. */
export function useStories() {
  const [stories, setStories] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStories = async () => {
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
    };

    fetchStories();
  }, []); 

  return { stories, loading, error };
}