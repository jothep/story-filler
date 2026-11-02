import {
  createContext,
  useCallback,
  useState,
  useContext,
  useRef,
  useEffect,
} from 'react';
import PropTypes from 'prop-types';

const StoryPlaybackContext = createContext(
  /** @type {import('../types').PlaybackState|undefined} */ (undefined)
);

export const useStoryPlayback = () => {
  const context = useContext(StoryPlaybackContext);
  if (context === undefined) {
    throw new Error(
      'useStoryPlayback must be used within a StoryPlaybackProvider'
    );
  }
  return context;
};

/** @param {import('react').RefObject<HTMLAudioElement|null>} audioRef */
function stopAudio(audioRef) {
  const audio = audioRef.current;
  audioRef.current = null;
  if (audio) {
    audio.onerror = null;
    audio.pause();
  }
}

/** @param {{story: import('../types').Story, children: import('react').ReactNode}} props */
export function StoryPlaybackProvider({ story, children }) {
  const [isMusicPlaying, setIsMusicPlaying] = useState(false);
  const [currentParagraphIndex, setCurrentParagraphIndex] = useState(0);
  const bgmAudioRef = useRef(/** @type {HTMLAudioElement|null} */ (null));
  const paragraphAudioRef = useRef(/** @type {HTMLAudioElement|null} */ (null));
  const musicRequestedRef = useRef(false);
  const musicRequestRef = useRef(0);

  /** @type {(audio: HTMLAudioElement) => Promise<void>} */
  const startBackgroundMusic = useCallback(async (audio) => {
    const request = ++musicRequestRef.current;
    musicRequestedRef.current = true;
    try {
      await audio.play();
      if (
        bgmAudioRef.current === audio &&
        musicRequestRef.current === request
      ) {
        setIsMusicPlaying(true);
      }
    } catch {
      if (
        bgmAudioRef.current === audio &&
        musicRequestRef.current === request
      ) {
        musicRequestedRef.current = false;
        setIsMusicPlaying(false);
      }
    }
  }, []);

  useEffect(() => {
    setIsMusicPlaying(false);
    if (!story?.background_music_url) return;

    const audio = new Audio(story.background_music_url);
    audio.loop = true;
    audio.volume = 0.3;
    bgmAudioRef.current = audio;
    audio.onerror = () => {
      if (bgmAudioRef.current !== audio) return;
      musicRequestRef.current += 1;
      musicRequestedRef.current = false;
      audio.pause();
      setIsMusicPlaying(false);
    };
    startBackgroundMusic(audio);

    return () => {
      musicRequestRef.current += 1;
      musicRequestedRef.current = false;
      stopAudio(bgmAudioRef);
    };
  }, [story, startBackgroundMusic]);

  useEffect(() => {
    setCurrentParagraphIndex(0);
    return () => stopAudio(paragraphAudioRef);
  }, [story]);

  const handleToggleMusic = () => {
    const audio = bgmAudioRef.current;
    if (!audio) return;
    if (musicRequestedRef.current) {
      // Invalidate a pending play as well as stopping established playback.
      musicRequestRef.current += 1;
      musicRequestedRef.current = false;
      audio.pause();
      setIsMusicPlaying(false);
    } else {
      startBackgroundMusic(audio);
    }
  };

  const handleNextParagraph = () => {
    stopAudio(paragraphAudioRef);
    const lastIndex = Math.max((story?.paragraphs?.length ?? 0) - 1, 0);
    setCurrentParagraphIndex((previous) => Math.min(previous + 1, lastIndex));
  };

  const handlePrevParagraph = () => {
    stopAudio(paragraphAudioRef);
    setCurrentParagraphIndex((previous) => Math.max(previous - 1, 0));
  };

  /** @param {string|null} audioUrl */
  const handlePlayParagraphAudio = async (audioUrl) => {
    if (!audioUrl) return;
    stopAudio(paragraphAudioRef);

    const audio = new Audio(audioUrl);
    audio.preload = 'auto';
    audio.crossOrigin = 'anonymous';
    paragraphAudioRef.current = audio;

    const reportFailure = () => {
      if (paragraphAudioRef.current !== audio) return;
      stopAudio(paragraphAudioRef);
      alert('Unable to play this audio. Please try again.');
    };
    audio.onerror = reportFailure;

    try {
      // Keep playback within the user's action; retries also use this button.
      await audio.play();
    } catch {
      reportFailure();
    }
  };

  const currentParagraph = story?.paragraphs?.[currentParagraphIndex] ?? null;
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
