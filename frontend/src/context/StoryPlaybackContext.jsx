// src/context/StoryPlaybackContext.jsx
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
  // 从 StoryPlayer.jsx 移动所有这些状态和 refs
  const [isMusicPlaying, setIsMusicPlaying] = useState(true);
  const bgmAudioRef = useRef(null);
  const paragraphAudioRef = useRef(null);
  const [currentParagraphIndex, setCurrentParagraphIndex] = useState(0);

  // 从 StoryPlayer.jsx 移动 BGM effect
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
  }, [story]); //

  // 从 StoryPlayer.jsx 移动所有处理函数
  const handleToggleMusic = () => {
    const audio = bgmAudioRef.current;
    if (!audio) return;
    const newMusicState = !isMusicPlaying;
    setIsMusicPlaying(newMusicState);
    newMusicState ? audio.play() : audio.pause();
  }; //

  const handleNextParagraph = () => {
    if (paragraphAudioRef.current) paragraphAudioRef.current.pause();
    if (story && story.paragraphs) {
      setCurrentParagraphIndex((prev) =>
        Math.min(prev + 1, story.paragraphs.length - 1)
      );
    }
  }; //

  const handlePrevParagraph = () => {
    if (paragraphAudioRef.current) paragraphAudioRef.current.pause();
    setCurrentParagraphIndex((prev) => Math.max(prev - 1, 0));
  }; //

  const handlePlayParagraphAudio = (audioUrl) => {
    if (!audioUrl) return;
    if (paragraphAudioRef.current) {
      paragraphAudioRef.current.pause();
      paragraphAudioRef.current = null;
    }
    const audio = new Audio(audioUrl);
    paragraphAudioRef.current = audio;
    audio.play().catch((e) => console.warn('段落音频播放失败:', e));
  }; //

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
  // 'story' 是一个对象，但根据你的要求，它不是必需的
  story: PropTypes.shape({
    background_music_url: PropTypes.string,
    paragraphs: PropTypes.array,
  }),
  // 'children' 是 React 节点，并且是必需的
  children: PropTypes.node.isRequired,
};

// (可选) 为 story 设置默认值
StoryPlaybackProvider.defaultProps = {
  story: null,
};