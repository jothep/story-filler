/**
 * Custom Hook: useBgmPlayer
 * Manages background music playback with autoplay and user controls
 */
import { useState, useEffect, useRef } from 'react';
import { getApiUrl } from '../config/api';
import { AUDIO } from '../constants/theme';

const buildBgmUrl = (audioUrl) => {
  if (audioUrl.startsWith('http')) {
    return audioUrl;
  }
  const apiBase = import.meta.env.VITE_API_URL || '';
  return `${apiBase}${audioUrl}`;
};

export const useBgmPlayer = () => {
  const [isMusicPlaying, setIsMusicPlaying] = useState(true);
  const [bgmPath, setBgmPath] = useState(null);
  const [showHint, setShowHint] = useState(false);
  const audioRef = useRef(null);

  // Fetch BGM configuration from API
  useEffect(() => {
    const fetchBgmConfig = async () => {
      try {
        const response = await fetch(getApiUrl('/api/config/'));
        if (!response.ok) {
          console.warn('Failed to fetch BGM config');
          return;
        }

        const config = await response.json();
        const audioUrl = config?.menu_bgm?.audio_url;

        if (audioUrl) {
          const fullUrl = buildBgmUrl(audioUrl);
          setBgmPath(fullUrl);
        }
      } catch (err) {
        console.warn('Error fetching BGM config:', err);
      }
    };

    fetchBgmConfig();
  }, []);

  // Initialize audio when BGM path is available
  useEffect(() => {
    if (!bgmPath) return;

    const audio = new Audio(bgmPath);
    audio.loop = true;
    audio.volume = AUDIO.DEFAULT_VOLUME;
    audioRef.current = audio;

    // Try autoplay
    audio.play()
      .then(() => setShowHint(false))
      .catch(() => {
        console.warn('Autoplay blocked - user interaction required');
        setIsMusicPlaying(false);
        setShowHint(true);
        setTimeout(() => setShowHint(false), AUDIO.HINT_DURATION_MS);
      });

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [bgmPath]);

  const toggleMusic = () => {
    const audio = audioRef.current;
    if (!audio) return;

    const shouldPlay = !isMusicPlaying;
    setIsMusicPlaying(shouldPlay);

    if (shouldPlay) {
      audio.play()
        .then(() => setShowHint(false))
        .catch((e) => {
          console.warn('Failed to play audio:', e);
          setIsMusicPlaying(false);
        });
    } else {
      audio.pause();
      setShowHint(false);
    }
  };

  return {
    isMusicPlaying,
    showHint,
    toggleMusic,
    hasBgm: !!bgmPath,
  };
};
