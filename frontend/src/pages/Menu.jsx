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
import logoImage from '../assets/story-filler-logo.png';

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
};

const logoStyles = {
  width: '600px',
  height: 'auto',
  maxWidth: '100%',
  maxHeight: '200px',
  objectFit: 'contain',
  display: 'block',
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
          <div style={{
            backgroundColor: '#F5DEB3',
            padding: '2rem 3rem',
            border: '6px solid #8B4513',
            borderRadius: '12px',
            boxShadow: '0 8px 16px rgba(0,0,0,0.3), inset 0 2px 4px rgba(255,255,255,0.5)',
            background: 'linear-gradient(135deg, #DEB887 0%, #D2691E 100%)',
            position: 'relative',
          }}>
            <div style={{
              position: 'absolute',
              top: '-8px',
              left: '20px',
              right: '20px',
              height: '4px',
              backgroundColor: '#654321',
              borderRadius: '2px',
            }} />
            <div style={{
              position: 'absolute',
              bottom: '-8px',
              left: '20px',
              right: '20px',
              height: '4px',
              backgroundColor: '#654321',
              borderRadius: '2px',
            }} />
            <h1 style={{
              fontFamily: '"Press Start 2P", cursive',
              fontSize: '2.5rem',
              color: '#FFD700',
              textShadow: '4px 4px 0 #654321, 6px 6px 0 rgba(0,0,0,0.3)',
              margin: 0,
              letterSpacing: '0.1em',
              textAlign: 'center',
            }}>
              STORY FILLER
            </h1>
            <div style={{
              marginTop: '0.5rem',
              fontSize: '0.875rem',
              color: '#8B4513',
              textAlign: 'center',
              fontFamily: '"Press Start 2P", cursive',
              letterSpacing: '0.2em',
            }}>
              ~ Fill The Blanks ~
            </div>
          </div>
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
        <div style={{
          backgroundColor: '#F5DEB3',
          padding: '2rem 3rem',
          border: '6px solid #8B4513',
          borderRadius: '12px',
          boxShadow: '0 8px 16px rgba(0,0,0,0.3), inset 0 2px 4px rgba(255,255,255,0.5)',
          background: 'linear-gradient(135deg, #DEB887 0%, #D2691E 100%)',
          position: 'relative',
        }}>
          <div style={{
            position: 'absolute',
            top: '-8px',
            left: '20px',
            right: '20px',
            height: '4px',
            backgroundColor: '#654321',
            borderRadius: '2px',
          }} />
          <div style={{
            position: 'absolute',
            bottom: '-8px',
            left: '20px',
            right: '20px',
            height: '4px',
            backgroundColor: '#654321',
            borderRadius: '2px',
          }} />
          <h1 style={{
            fontFamily: '"Press Start 2P", cursive',
            fontSize: '2.5rem',
            color: '#FFD700',
            textShadow: '4px 4px 0 #654321, 6px 6px 0 rgba(0,0,0,0.3)',
            margin: 0,
            letterSpacing: '0.1em',
            textAlign: 'center',
          }}>
            STORY FILLER
          </h1>
          <div style={{
            marginTop: '0.5rem',
            fontSize: '0.875rem',
            color: '#8B4513',
            textAlign: 'center',
            fontFamily: '"Press Start 2P", cursive',
            letterSpacing: '0.2em',
          }}>
            ~ Fill The Blanks ~
          </div>
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
