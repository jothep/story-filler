// src/components/WordList.jsx
import PropTypes from 'prop-types';
import { useDraggable } from '@dnd-kit/core';

//
// --- 👇 修复点 1：在这里接收 onWordSelect ---
//
function DraggableWordButton({ word, onWordSelect }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: word.id,
  });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 99,
      }
    : undefined;

  return (
    <button
      type="button"
      className="nes-btn"
      key={word.id}
      onClick={() => onWordSelect(word)}
      ref={setNodeRef}
      style={{ ...style, flexGrow: 1 }}
      {...listeners}
      {...attributes}
    >
      {word.maori_word}
    </button>
  );
}

DraggableWordButton.propTypes = {
  word: PropTypes.shape({
    id: PropTypes.number.isRequired,
    maori_word: PropTypes.string.isRequired,
  }).isRequired,
  onWordSelect: PropTypes.func.isRequired,
};

function WordList({ words, onWordSelect }) {
  if (!words) {
    return <div>Loading words...</div>;
  }

  return (
    <div
      className="nes-container is-dark"
      style={{
        height: '100%',
        boxSizing: 'border-box',
        overflowY: 'auto',
        padding: '0.5rem',
      }}
    >
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {words.map((word) => (
          <DraggableWordButton
            key={word.id}
            word={word}
            onWordSelect={onWordSelect}
          />
        ))}
      </div>
    </div>
  );
}

WordList.propTypes = {
  words: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      maori_word: PropTypes.string.isRequired,
    })
  ).isRequired,
  onWordSelect: PropTypes.func.isRequired,
};

export default WordList;
