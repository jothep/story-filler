// src/components/WordList.jsx
import PropTypes from 'prop-types';
import { useDraggable, useDndContext } from '@dnd-kit/core'; 
import { useWordInteraction } from '../context/WordInteractionContext';

function DraggableWordButton({ word }) {
  const { setSelectedWord } = useWordInteraction();
  
  const { attributes, listeners, setNodeRef } =
    useDraggable({
      id: word.id,
    });

  const { active } = useDndContext();
  const isDragging = active && active.id === word.id;

  const style = {
    width: 'auto', 
    visibility: isDragging ? 'hidden' : 'visible', 
    zIndex: 'auto', 
  };

  const button = (
    <button
      type="button"
      className="nes-btn"
      key={word.id}
      onClick={() => setSelectedWord(word)}
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
    >
      {word.maori_word}
    </button>
  );

  return button;
}

DraggableWordButton.propTypes = {
  word: PropTypes.shape({
    id: PropTypes.number.isRequired,
    maori_word: PropTypes.string.isRequired,
  }).isRequired,
};

function WordList({ words }) {
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
        overflowX: 'hidden',
        padding: '0.5rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0.5rem',
        }}
      >
        {words.map((word) => (
          <DraggableWordButton
            key={word.id}
            word={word}
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
  ), 
};

WordList.defaultProps = {
  words: [],
};

export default WordList;