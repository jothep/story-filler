// src/pages/Menu.jsx
// Renders the main menu screen. It uses the `useStories` hook to fetch and
// display a list of story links, and manages background music (BGM) playback
// with a toggle control. Also includes the <Roll> background component.
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import Roll from '../components/Roll';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import '../components/Roll.css';
import { useStories } from '../hooks/useStories';
import { getApiUrl } from '../config/api';
import logoImage from '../assets/story-filler-logo-final.png';

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
  marginBottom: '2rem',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  position: 'relative',
  zIndex: 10,
};

const toggleContainerStyles = {
  position: 'absolute',
  top: '1.5rem',
  right: '1.5rem',
  zIndex: 20,
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
  position: 'relative',
  zIndex: 10,
};

function Menu() {
  const { stories, loading, error, refetch } = useStories();

  const [isMusicPlaying, setIsMusicPlaying] = useState(false);
  const [bgmPath, setBgmPath] = useState(null);
  const audioRef = useRef(null);

  // Fetch BGM configuration from API
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch(getApiUrl('/api/config/'));
        if (response.ok) {
          const config = await response.json();
          // Use the audio_url from the menu_bgm object
          if (config.menu_bgm && config.menu_bgm.audio_url) {
            setBgmPath(config.menu_bgm.audio_url);
          }
        } else {
          console.warn('Failed to fetch BGM config, BGM will be disabled');
        }
      } catch (err) {
        console.warn('Error fetching BGM config:', err);
      }
    };

    fetchConfig();
  }, []);

  // Initialize audio when BGM path is available
  useEffect(() => {
    if (!bgmPath) {
      return;
    }

    const audio = new Audio(bgmPath);
    audio.loop = true;
    audio.volume = 0.3;
    audioRef.current = audio;

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [bgmPath]);

  const handleToggleMusic = () => {
    const audio = audioRef.current;
    if (!audio) return;

    const newMusicState = !isMusicPlaying;
    setIsMusicPlaying(newMusicState);

    if (newMusicState) {
      audio.play().catch((e) => {
        console.warn('Failed to play audio:', e);
        setIsMusicPlaying(false);
      });
    } else {
      audio.pause();
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading stories..." />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />;
  }

  if (!stories || stories.length === 0) {
    return (
      <div style={menuStyles}>
        <Roll />
        <div style={titleContainerStyles}>
          <img
            src={logoImage}
            alt="Story Filler"
            style={{
              width: '500px',
              height: 'auto',
            }}
          />
        </div>
        <div className="nes-container is-rounded" style={{ textAlign: 'center', maxWidth: '500px' }}>
          <h2>No Stories Available</h2>
          <p>There are currently no stories to display. Please check back later!</p>
        </div>
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
        <img
          src={logoImage}
          alt="Story Filler"
          style={{
            width: '500px',
            height: 'auto',
          }}
        />
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
