import { useState, useEffect, useRef, useCallback } from 'react';
import { getApiUrl } from '../config/api';
import { AUDIO } from '../constants/theme';
import { isAbortError } from '../utils/errors';

/** @param {string} audioUrl */
const buildBgmUrl = (audioUrl) => {
  if (audioUrl.startsWith('http')) return audioUrl;
  const apiBase = import.meta.env.VITE_API_URL || '';
  return `${apiBase}${audioUrl}`;
};

export const useBgmPlayer = () => {
  const [isMusicPlaying, setIsMusicPlaying] = useState(false);
  const [bgmPath, setBgmPath] = useState(/** @type {string|null} */ (null));
  const [showHint, setShowHint] = useState(false);
  const audioRef = useRef(/** @type {HTMLAudioElement|null} */ (null));
  const playRequestedRef = useRef(false);
  const playRequestRef = useRef(0);
  const hintTimerRef = useRef(/** @type {number|undefined} */ (undefined));

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    const fetchBgmConfig = async () => {
      try {
        const response = await fetch(getApiUrl('/api/config/'), {
          signal: controller.signal,
        });
        if (!response.ok) return;
        const config = await response.json();
        const audioUrl = config?.menu_bgm?.audio_url;
        if (active && typeof audioUrl === 'string' && audioUrl) {
          setBgmPath(buildBgmUrl(audioUrl));
        }
      } catch (error) {
        if (active && !isAbortError(error)) {
          console.warn('Unable to load background music configuration.');
        }
      }
    };

    fetchBgmConfig();
    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  const clearHintTimer = useCallback(() => {
    clearTimeout(hintTimerRef.current);
    hintTimerRef.current = undefined;
  }, []);

  /** @type {(audio: HTMLAudioElement) => Promise<void>} */
  const playMusic = useCallback(
    async (audio) => {
      const request = ++playRequestRef.current;
      playRequestedRef.current = true;
      clearHintTimer();
      setShowHint(false);

      try {
        await audio.play();
        if (audioRef.current === audio && playRequestRef.current === request) {
          setIsMusicPlaying(true);
        }
      } catch {
        if (audioRef.current !== audio || playRequestRef.current !== request)
          return;
        playRequestedRef.current = false;
        setIsMusicPlaying(false);
        setShowHint(true);
        hintTimerRef.current = setTimeout(() => {
          setShowHint(false);
          hintTimerRef.current = undefined;
        }, AUDIO.HINT_DURATION_MS);
      }
    },
    [clearHintTimer]
  );

  useEffect(() => {
    if (!bgmPath) return;
    const audio = new Audio(bgmPath);
    audio.loop = true;
    audio.volume = AUDIO.DEFAULT_VOLUME;
    audioRef.current = audio;
    audio.onerror = () => {
      if (audioRef.current !== audio) return;
      playRequestRef.current += 1;
      playRequestedRef.current = false;
      audio.pause();
      clearHintTimer();
      setShowHint(false);
      setIsMusicPlaying(false);
    };
    playMusic(audio);

    return () => {
      playRequestRef.current += 1;
      playRequestedRef.current = false;
      audioRef.current = null;
      audio.onerror = null;
      audio.pause();
      clearHintTimer();
    };
  }, [bgmPath, playMusic, clearHintTimer]);

  const toggleMusic = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (playRequestedRef.current) {
      playRequestRef.current += 1;
      playRequestedRef.current = false;
      audio.pause();
      clearHintTimer();
      setShowHint(false);
      setIsMusicPlaying(false);
    } else {
      playMusic(audio);
    }
  };

  return { isMusicPlaying, showHint, toggleMusic, hasBgm: !!bgmPath };
};
