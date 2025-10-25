import { useState, useEffect } from 'react';
import { getStoryById } from '../api/storyApi'; 

 /* Custom hook to fetch and manage the state for a single story. */
export function useStory(storyId) {
  const [story, setStory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!storyId) {
      setLoading(false);
      return;
    }

    const fetchStory = async () => {
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
    };

    fetchStory();

  }, [storyId]); 

  return { story, loading, error };
}