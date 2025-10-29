// src/components/WordAudio.jsx
// Renders playback controls for the selected word, pulling the
// `selectedWord` from the `WordInteractionContext` to play
// both its Māori and English audio.
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
          <div>
            <button
              type="button"
              className="nes-btn is-warning" 
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
              className="nes-btn is-warning" 
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

export default WordAudio;