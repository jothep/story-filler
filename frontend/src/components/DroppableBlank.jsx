// src/components/DroppableBlank.jsx
// A droppable component (using `dnd-kit`) that represents a fillable blank.
// It dynamically changes its style (color, animation) based on whether
// it is filled correctly, incorrectly, or being hovered over.
import PropTypes from 'prop-types';

import { useDroppable, useDndContext } from '@dnd-kit/core'; 

function DroppableBlank({ blank, uniqueId, filledWord, isWrong }) {
  const { isOver, setNodeRef } = useDroppable({
    id: uniqueId,
    data: {
      type: 'blank',
      correctWordId: blank.word.id,
    },
    disabled: !!filledWord,
  });

  const { active } = useDndContext(); // Detect if anything is being dragged
  const isDragging = !!active; // True if any word is being dragged

  const colors = {
    default: '#adb5bd',
    correct: '#92cc41',
    wrong: '#e76e55',
    hover: '#333',
    dragging: '#ffd700', // Yellow when dragging
  };

  let borderColor = colors.default;
  let textColor = colors.default;

  if (filledWord) {
    borderColor = colors.correct;
    textColor = colors.correct;
  } else if (isWrong) {
    borderColor = colors.wrong;
  } else if (isDragging && !filledWord) {
    // Empty blanks turn yellow when any word is being dragged
    borderColor = colors.dragging;
  }

  const style = {
    display: 'inline-block',
    margin: '0 0.25rem',
    minWidth: '150px',

    height: '3.5rem',

    verticalAlign: 'middle',

    backgroundColor: isOver ? colors.hover : 'transparent',

    borderRadius: '4px',
    boxSizing: 'border-box',

    border: `3px solid ${borderColor}`,

    color: textColor,

    animation: isWrong ? 'shake 0.5s' : (isOver ? 'pulse 0.6s ease-in-out' : 'none'),

    padding: 0,
    textAlign: 'center',
    fontWeight: 'bold',

    fontSize: 'inherit',

    lineHeight: 'calc(3.5rem - 6px)',

    transition: 'border-color 0.2s ease, transform 0.2s ease',
    transform: isOver ? 'scale(1.02)' : 'scale(1)',
  };

  return (
    <span ref={setNodeRef} style={style}>
      {filledWord ? filledWord.maori_word : null}
    </span>
  );
}

DroppableBlank.propTypes = {
  blank: PropTypes.shape({
    word: PropTypes.shape({
      id: PropTypes.number.isRequired,
    }).isRequired,
  }).isRequired,
  uniqueId: PropTypes.string.isRequired,
  filledWord: PropTypes.shape({
    maori_word: PropTypes.string.isRequired,
  }),
  isWrong: PropTypes.bool.isRequired,
};

export default DroppableBlank;