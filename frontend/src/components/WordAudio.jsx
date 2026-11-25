import { useCallback, useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { useWordInteraction } from '../context/WordInteractionContext';
import { wordText } from '../utils/words';

/**
 * @typedef {object} AudioRow
 * @property {string} language
 * @property {string} text
 * @property {string|null} audio
 */

/**
 * Plays a word in the story's learning language and, when the story is
 * written in another language, its translation.
 *
 * @param {{learningLanguage?: import('../types').Language|null,
 *   storyLanguage?: import('../types').Language|null}} props
 */
function WordAudio({ learningLanguage = null, storyLanguage = null }) {
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

  const learningName = learningLanguage?.name ?? 'Word';
  const storyName = storyLanguage?.name ?? 'Translation';
  const showTranslation =
    !learningLanguage ||
    !storyLanguage ||
    learningLanguage.code !== storyLanguage.code;

  /** @type {AudioRow[]} */
  const rows = selectedWord
    ? [
        {
          language: learningName,
          text: wordText(selectedWord),
          audio: selectedWord.audio,
        },
        {
          language: storyName,
          text: selectedWord.translation ?? '',
          audio: selectedWord.translation_audio,
        },
      ]
    : [
        { language: learningName, text: `${learningName} word`, audio: null },
        { language: storyName, text: `${storyName} word`, audio: null },
      ];

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
      {rows.slice(0, showTranslation ? 2 : 1).map((row) => (
        <div key={row.language}>
          <button
            type="button"
            className={`nes-btn ${row.audio ? 'is-primary' : 'is-disabled'}`}
            disabled={!row.audio}
            aria-label={`Play ${row.language} audio`}
            title={`Play ${row.language} audio`}
            style={{ marginRight: '1rem' }}
            onClick={() => playAudio(row.audio)}
          >
            play
          </button>
          <span>{row.text}</span>
        </div>
      ))}
      {audioError && <p role="status">{audioError}</p>}
    </div>
  );
}

const languageShape = PropTypes.shape({
  code: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
});

WordAudio.propTypes = {
  learningLanguage: languageShape,
  storyLanguage: languageShape,
};

export default WordAudio;
