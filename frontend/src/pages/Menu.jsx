// src/pages/Menu.jsx
// Renders the main menu screen. It uses the `useStories` hook to fetch and
// display a list of story links, and manages background music (BGM) playback
// with a toggle control. Also includes the <Roll> background component.
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import Roll from '../components/Roll'; 
import '../components/Roll.css'; 
import { useStories } from '../hooks/useStories';

const menuStyles = {
  position: 'relative', 
  overflow: 'hidden',

  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '2rem',
  minHeight: '100vh',
  boxSizing: 'border-box', 
};

const titleContainerStyles = {
  width: '100%',
  maxWidth: '800px',
  marginBottom: '4rem', 

  backgroundColor: 'rgba(255, 255, 255, 0.8)', 
  padding: '1rem',
  borderRadius: '4px',
};

const toggleContainerStyles = {
  position: 'absolute',
  top: '1.5rem',
  right: '1.5rem',
  zIndex: 10,
  color: 'white',
  textShadow: '1px 1px #000',
};

const menuListStyles = {
  display: 'flex',
  flexDirection: 'column',
  width: '100%',
  maxWidth: '400px', 
  gap: '1.5rem', 
  marginTop: 'auto',  
  marginBottom: '20vh',
};

function Menu() {
  const { stories, loading, error } = useStories();

  const [isMusicPlaying, setIsMusicPlaying] = useState(true);
  const audioRef = useRef(null);

  useEffect(() => {
    const audio = new Audio('/media/bgm/Schumann_Fantasy.mp3');

    audio.loop = true;
    audio.volume = 0.3;
    audioRef.current = audio;

    if (isMusicPlaying) {
      audio.play().catch((e) => {
        console.warn('The browser blocks autoplay:', e);
      });
    }

    return () => {
      audio.pause();
      audioRef.current = null;
    };
  }, []); 

  const handleToggleMusic = () => {
    const audio = audioRef.current;
    if (!audio) return;

    const newMusicState = !isMusicPlaying;
    setIsMusicPlaying(newMusicState);

    if (newMusicState) {
      audio.play();
    } else {
      audio.pause();
    }
  };

  if (loading) {
    return <div style={{ padding: '2rem' }}>Loading stories...</div>;
  }

  if (error) {
    return (
      <div style={{ color: 'red', padding: '2rem' }}>
        Error loading stories: {error}
      </div>
    );
  }

  return (
    <div style={menuStyles}>
      <Roll />
      <div style={toggleContainerStyles}>
        <label>
          <input
            type="checkbox"
            className="nes-checkbox"
            checked={isMusicPlaying}
            onChange={handleToggleMusic}
          />
          <span>BGM</span>
        </label>
      </div>
      <div style={titleContainerStyles}>
        <div
          className="nes-container is-centered"
          style={{ backgroundColor: 'white' }}
        >
          <h1>Story Filler</h1>
        </div>
      </div>
      <div style={menuListStyles}>
        {stories.map((story) => (
          <Link
            key={story.id}
            to={`/story/${story.id}`}
            className="nes-btn is-primary" 
          >
            {story.title}
          </Link>
        ))}
      </div>
    </div>
  );
}

export default Menu;
