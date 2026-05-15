// src/context/StoryPlaybackContext.jsx
// Defines a React Context (`StoryPlaybackProvider`) that encapsulates all state
// and logic for story playback, including BGM, paragraph navigation, and
// paragraph audio. Exports `useStoryPlayback` to consume this state.
import { createContext, useState, useContext, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';


const StoryPlaybackContext = createContext();

export const useStoryPlayback = () => {
  const context = useContext(StoryPlaybackContext);
  if (context === undefined) {
    throw new Error('useStoryPlayback must be used within a StoryPlaybackProvider');
  }
  return context;
};

export function StoryPlaybackProvider({ story, children }) {
  const [isMusicPlaying, setIsMusicPlaying] = useState(true);
  const bgmAudioRef = useRef(null);
  const paragraphAudioRef = useRef(null);
  const [currentParagraphIndex, setCurrentParagraphIndex] = useState(0);

  useEffect(() => {
    if (!story || !story.background_music_url) {
      return;
    }
    const audio = new Audio(story.background_music_url);
    audio.loop = true;
    audio.volume = 0.3;
    bgmAudioRef.current = audio;

    if (isMusicPlaying) {
      audio.play().catch((e) => console.warn('BGM 自动播放被阻止:', e));
    }
    return () => {
      audio.pause();
      bgmAudioRef.current = null;
    };
  }, [story]); 

  const handleToggleMusic = () => {
    const audio = bgmAudioRef.current;
    if (!audio) return;
    const newMusicState = !isMusicPlaying;
    setIsMusicPlaying(newMusicState);
    newMusicState ? audio.play() : audio.pause();
  }; 

  const handleNextParagraph = () => {
    if (paragraphAudioRef.current) paragraphAudioRef.current.pause();
    if (story && story.paragraphs) {
      setCurrentParagraphIndex((prev) =>
        Math.min(prev + 1, story.paragraphs.length - 1)
      );
    }
  }; 

  const handlePrevParagraph = () => {
    if (paragraphAudioRef.current) paragraphAudioRef.current.pause();
    setCurrentParagraphIndex((prev) => Math.max(prev - 1, 0));
  }; 

  const handlePlayParagraphAudio = (audioUrl) => {
    if (!audioUrl) {
      console.warn('No audio URL provided');
      return;
    }

    console.log('Attempting to play audio:', audioUrl);

    // Stop any currently playing paragraph audio
    if (paragraphAudioRef.current) {
      paragraphAudioRef.current.pause();
      paragraphAudioRef.current.currentTime = 0;
      paragraphAudioRef.current = null;
    }

    const audio = new Audio(audioUrl);
    paragraphAudioRef.current = audio;

    // Set audio properties for better iOS compatibility
    audio.preload = 'auto';
    audio.crossOrigin = 'anonymous';

    // Error handling
    audio.addEventListener('error', (e) => {
      console.error('Audio error:', {
        error: e,
        audioUrl: audioUrl,
        errorCode: audio.error?.code,
        errorMessage: audio.error?.message
      });

      let errorMsg = 'Unable to play audio. ';
      if (audio.error?.code === 4) {
        errorMsg += 'Audio format not supported. Please convert to MP3.';
      } else if (audio.error?.code === 2) {
        errorMsg += 'Network error loading audio.';
      } else {
        errorMsg += 'Please check your internet connection.';
      }
      alert(errorMsg);
    }, { once: true });

    // iOS/iPad Safari requires explicit user interaction
    // Try to play immediately (works if triggered by user action)
    const playPromise = audio.play();

    if (playPromise !== undefined) {
      playPromise
        .then(() => {
          console.log('Audio playing successfully');
        })
        .catch((e) => {
          console.error('Failed to play paragraph audio:', e);
          // If autoplay fails, try loading first then playing
          audio.load();
          audio.addEventListener('canplaythrough', () => {
            audio.play().catch((err) => {
              console.error('Still failed after load:', err);
              alert('Audio playback failed. File format may not be supported on this device.');
            });
          }, { once: true });
        });
    }
  }; 

  const currentParagraph = (story && story.paragraphs && story.paragraphs.length > 0)
    ? story.paragraphs[currentParagraphIndex]
    : null;

  const value = {
    story, 
    isMusicPlaying,
    currentParagraph,
    currentParagraphIndex,
    handleToggleMusic,
    handleNextParagraph,
    handlePrevParagraph,
    handlePlayParagraphAudio,
  };

  return (
    <StoryPlaybackContext.Provider value={value}>
      {children}
    </StoryPlaybackContext.Provider>
  );
}

StoryPlaybackProvider.propTypes = {
  story: PropTypes.shape({
    background_music_url: PropTypes.string,
    paragraphs: PropTypes.array,
  }),
  children: PropTypes.node.isRequired,
};

StoryPlaybackProvider.defaultProps = {
  story: null,
};