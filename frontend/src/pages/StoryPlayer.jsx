// src/pages/StoryPlayer.jsx
// This component acts as a controller for the story playing experience.
// It fetches the specific story data using `useStory` (based on the URL `storyId`),
// handles loading/error states, and sets up the necessary context providers
import { useParams } from 'react-router-dom';
import '../assets/StoryPlayer.css';
import StoryPlayerUI from './StoryPlayerUI';
import { useStory } from '../hooks/useStory';

import { WordInteractionProvider } from '../context/WordInteractionContext'; 
import { StoryPlaybackProvider } from '../context/StoryPlaybackContext';

function StoryPlayer() {
  const { storyId } = useParams();
  const { story, loading, error } = useStory(storyId);

  if (loading) {
    return <div style={{ color: 'white', padding: '2rem' }}>Loading story...</div>; //
  }
  if (error) {
    return <div style={{ color: 'red', padding: '2rem' }}>Error loading story: {error}</div>; //
  }
  if (!story) {
    return <div>No story found.</div>; //
  }

  return (
    <StoryPlaybackProvider story={story}>
      <WordInteractionProvider wordsInBank={story.words_in_bank}>

        <StoryPlayerUI />

      </WordInteractionProvider>
    </StoryPlaybackProvider>
  );
}

export default StoryPlayer;
