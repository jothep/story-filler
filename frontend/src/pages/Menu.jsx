// src/pages/Menu.jsx
// Renders the main menu screen. It uses the `useStories` hook to fetch and
// display a list of story links, and manages background music (BGM) playback
// with a toggle control. Also includes the <Roll> background component.
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import Roll from '../components/Roll';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import InfoCredits from '../components/InfoCredits';
import '../components/Roll.css';
import '../components/BgmHint.css';
import { useStories } from '../hooks/useStories';
import { getApiUrl } from '../config/api';
import logoImage from '../assets/story-filler-logo-single-line.png';

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
  marginBottom: '0.5rem',
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

const bgmHintStyles = {
  position: 'absolute',
  top: '4.5rem',
  right: '1.5rem',
  zIndex: 20,
  background: 'rgba(0, 0, 0, 0.8)',
  color: '#FFE4B5',
  padding: '0.5rem 1rem',
  borderRadius: '4px',
  fontSize: '0.75rem',
  whiteSpace: 'nowrap',
  animation: 'fadeIn 0.3s ease-in',
};

const infoButtonContainerStyles = {
  width: '100%',
  display: 'flex',
  justifyContent: 'center',
  marginBottom: '1rem',
  position: 'relative',
  zIndex: 10,
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

  const [isMusicPlaying, setIsMusicPlaying] = useState(true);
  const [bgmPath, setBgmPath] = useState(null);
  const [showBgmHint, setShowBgmHint] = useState(false);
  const audioRef = useRef(null);

  // Fetch BGM configuration from API
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch(getApiUrl('/api/config/'));
        if (response.ok) {
          const config = await response.json();
          console.log('BGM config received:', config);
          // Use the audio_url from the menu_bgm object
          if (config.menu_bgm && config.menu_bgm.audio_url) {
            // Build full URL for media file
            let fullUrl;
            if (config.menu_bgm.audio_url.startsWith('http')) {
              fullUrl = config.menu_bgm.audio_url;
            } else {
              // For relative paths like /media/..., prepend API base URL
              const apiBase = import.meta.env.VITE_API_URL || '';
              fullUrl = `${apiBase}${config.menu_bgm.audio_url}`;
            }
            console.log('BGM URL:', fullUrl);
            setBgmPath(fullUrl);
          } else {
            console.warn('No menu_bgm in config');
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
      console.log('No BGM path yet');
      return;
    }

    console.log('Initializing audio with path:', bgmPath);
    const audio = new Audio(bgmPath);
    audio.loop = true;
    audio.volume = 0.3;
    audioRef.current = audio;

    // Try to auto-play BGM when loaded
    // Note: Browsers may block autoplay until user interaction
    audio.play().then(() => {
      console.log('BGM autoplay started successfully');
      setShowBgmHint(false);
    }).catch((e) => {
      console.warn('Autoplay blocked by browser. Click BGM checkbox to start:', e);
      setIsMusicPlaying(false);
      setShowBgmHint(true);
      // Auto-hide hint after 5 seconds
      setTimeout(() => setShowBgmHint(false), 5000);
    });

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [bgmPath]);

  const handleToggleMusic = () => {
    console.log('Toggle music clicked, current state:', isMusicPlaying);
    const audio = audioRef.current;
    if (!audio) {
      console.warn('No audio ref available');
      return;
    }

    const newMusicState = !isMusicPlaying;
    console.log('New music state will be:', newMusicState);
    setIsMusicPlaying(newMusicState);

    if (newMusicState) {
      console.log('Attempting to play audio');
      audio.play().then(() => {
        console.log('Audio playing successfully');
        setShowBgmHint(false);
      }).catch((e) => {
        console.warn('Failed to play audio:', e);
        setIsMusicPlaying(false);
      });
    } else {
      console.log('Pausing audio');
      audio.pause();
      setShowBgmHint(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading stories..." />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />;
  }

  // Render unified menu layout
  return (
    <div style={menuStyles}>
      <Roll />

      {/* BGM Control */}
      <div style={toggleContainerStyles}>
        <label>
          <input
            type="checkbox"
            className="nes-checkbox is-dark"
            checked={isMusicPlaying}
            onChange={handleToggleMusic}
          />
          <span>BGM</span>
        </label>
      </div>

      {/* BGM Hint */}
      {showBgmHint && (
        <div style={bgmHintStyles}>
          Click to start music ⇑
        </div>
      )}

      {/* Logo */}
      <div style={titleContainerStyles}>
        <img
          src={logoImage}
          alt="Story Filler"
          style={{
            width: '700px',
            height: 'auto',
          }}
        />
      </div>

      {/* Info/Credits Button */}
      <div style={infoButtonContainerStyles}>
        <InfoCredits />
      </div>

      {/* Story List or No Stories Message */}
      {(!stories || stories.length === 0) ? (
        <div className="nes-container is-rounded" style={{ textAlign: 'center', maxWidth: '500px', position: 'relative', zIndex: 10 }}>
          <h2>No Stories Available</h2>
          <p>There are currently no stories to display. Please check back later!</p>
        </div>
      ) : (
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
      )}
    </div>
  );
}

export default Menu;
