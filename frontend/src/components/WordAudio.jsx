import { useCallback, useEffect, useRef, useState } from 'react';
import { useWordInteraction } from '../context/WordInteractionContext';

function WordAudio() {
  const { selectedWord } = useWordInteraction();
  const audioRef = useRef(/** @type {HTMLAudioElement|null} */ (null));
  const [audioError, setAudioError] = useState(
    /** @type {string|null} */ (null)
  );

  const stopAudio = useCallback(() => {
    const audio = audioRef.current;
    audioRef.current = null;
    if (audio) {
      audio.onerror = null;
      audio.pause();
    }
  }, []);

  useEffect(() => {
    setAudioError(null);
    return stopAudio;
  }, [selectedWord, stopAudio]);

  /** @param {string|null} audioSrc */
  const playAudio = async (audioSrc) => {
    if (!audioSrc) return;
    stopAudio();
    setAudioError(null);
    const audio = new Audio(audioSrc);
    audioRef.current = audio;

    const reportFailure = () => {
      if (audioRef.current !== audio) return;
      stopAudio();
      setAudioError('Unable to play this recording. Please try again.');
    };
    audio.onerror = reportFailure;
    try {
      await audio.play();
    } catch {
      reportFailure();
    }
  };

  return (
    <div
      className="nes-container is-dark"
      style={{
        height: '100%',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-around',
        padding: '0.5rem 1rem',
      }}
    >
      {selectedWord ? (
        <>
          <div>
            <button
              type="button"
              className={`nes-btn ${selectedWord.maori_audio ? 'is-primary' : 'is-disabled'}`}
              disabled={!selectedWord.maori_audio}
              style={{ marginRight: '1rem' }}
              onClick={() => playAudio(selectedWord.maori_audio)}
            >
              play
            </button>
            <span>{selectedWord.maori_word}</span>
          </div>

          <div>
            <button
              type="button"
              className={`nes-btn ${selectedWord.english_audio ? 'is-primary' : 'is-disabled'}`}
              disabled={!selectedWord.english_audio}
              style={{ marginRight: '1rem' }}
              onClick={() => playAudio(selectedWord.english_audio)}
            >
              play
            </button>
            <span>{selectedWord.english_translation}</span>
          </div>
        </>
      ) : (
        <>
          <div>
            <button
              type="button"
              className="nes-btn is-disabled"
              disabled
              style={{ marginRight: '1rem' }}
            >
              play
            </button>
            <span>maori word</span>
          </div>
          <div>
            <button
              type="button"
              className="nes-btn is-disabled"
              disabled
              style={{ marginRight: '1rem' }}
            >
              play
            </button>
            <span>english word</span>
          </div>
        </>
      )}
      {audioError && <p role="status">{audioError}</p>}
    </div>
  );
}

export default WordAudio;
