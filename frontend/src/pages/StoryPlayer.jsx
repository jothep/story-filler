// src/pages/StoryPlayer.jsx
// This component acts as a controller for the story playing experience.
// It fetches the specific story data using `useStory` (based on the URL `storyId`),
// handles loading/error states, and sets up the necessary context providers
import { useParams } from 'react-router-dom';
import '../assets/StoryPlayer.css';
import '../assets/StoryPlayer.mobile.css';
import StoryPlayerUI from './StoryPlayerUI';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { useStory } from '../hooks/useStory';

import { WordInteractionProvider } from '../context/WordInteractionContext';
import { StoryPlaybackProvider } from '../context/StoryPlaybackContext';

function StoryPlayer() {
  const { storyId } = useParams();
  const { story, loading, error, refetch } = useStory(storyId);

  if (loading) {
    return <LoadingSpinner message="Loading story..." />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />;
  }

  if (!story) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '2rem'
      }}>
        <div className="nes-container is-rounded" style={{ textAlign: 'center' }}>
          <h2>Story Not Found</h2>
          <p>The requested story could not be loaded.</p>
        </div>
      </div>
    );
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
