// src/components/WordAudio.jsx
import PropTypes from 'prop-types';
import { useWordInteraction } from '../context/WordInteractionContext';

function WordAudio() {
  const { selectedWord } = useWordInteraction();
  const playAudio = (audioSrc) => {
    if (audioSrc) {
      const audio = new Audio(audioSrc);
      audio.play();
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
          {/* --- 这是修改后的 maori 部分 --- */}
          <div>
            <button
              type="button"
              className="nes-btn is-warning" /* 'is-warning' 是橙色 */
              style={{ marginRight: '1rem' }}
              onClick={() => playAudio(selectedWord.maori_audio)}
            >
              play
            </button>
            <span>{selectedWord.maori_word}</span>
          </div>

          {/* --- 这是修改后的 english 部分 --- */}
          <div>
            <button
              type="button"
              className="nes-btn is-warning" /* 'is-warning' 是橙色 */
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
          {/* --- 这部分(占位符)保持不变 --- */}
          <div>
            <button
              type="button"
              className="nes-btn is-disabled"
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
              style={{ marginRight: '1rem' }}
            >
              play
            </button>
            <span>english word</span>
          </div>
        </>
      )}
    </div>
  );
}

WordAudio.propTypes = {

};

export default WordAudio;