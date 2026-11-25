import { useState } from 'react';
import { useWordInteraction } from '../context/WordInteractionContext';
import { wordText } from '../utils/words';

function WordPic() {
  const { selectedWord } = useWordInteraction();
  const [failedImage, setFailedImage] = useState(
    /** @type {string|null} */ (null)
  );
  const image = selectedWord?.image ?? null;
  const showImage = Boolean(image) && image !== failedImage;

  /** @type {import('react').CSSProperties} */
  const containerStyle = {
    height: '100%',
    width: '100%',
    boxSizing: 'border-box',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0.5rem',
    overflow: 'hidden',
  };

  /** @type {import('react').CSSProperties} */
  const imageStyle = {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
  };

  let content = <p>word pic</p>;
  if (selectedWord && showImage) {
    content = (
      <img
        src={image ?? undefined}
        alt={selectedWord.translation || wordText(selectedWord)}
        style={imageStyle}
        onError={() => setFailedImage(image)}
      />
    );
  } else if (selectedWord) {
    // A word may not have a picture yet; show that instead of a broken image.
    content = <p className="nes-text is-disabled">No picture yet</p>;
  }

  return (
    <div className="nes-container is-dark" style={containerStyle}>
      {content}
    </div>
  );
}

export default WordPic;
