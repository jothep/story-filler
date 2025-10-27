// src/components/WordPic.jsx
import { useWordInteraction } from '../context/WordInteractionContext';

function WordPic() {
  const { selectedWord } = useWordInteraction();

  const containerStyle = {
    height: '100%',
    width: '100%',
    boxSizing: 'border-box',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0.5rem',
    overflow: 'hidden',
  }; //

  const imageStyle = {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
  }; //

  return (
    <div
      className="nes-container is-dark"
      style={containerStyle} //
    >
      {selectedWord ? (
        <img
          src={selectedWord.image} //
          alt={selectedWord.english_translation} //
          style={imageStyle} //
        />
      ) : (
        <p>word pic</p> //
      )}
    </div>
  );
}

export default WordPic;