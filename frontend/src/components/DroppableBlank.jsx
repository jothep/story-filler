// src/components/DroppableBlank.jsx
// A droppable component (using `dnd-kit`) that represents a fillable blank.
// It dynamically changes its style (color, animation) based on whether
// it is filled correctly, incorrectly, or being hovered over.
import PropTypes from 'prop-types';

import { useDroppable } from '@dnd-kit/core'; 

function DroppableBlank({ blank, uniqueId, filledWord, isWrong }) {
  const { isOver, setNodeRef } = useDroppable({
    id: uniqueId,
    data: {
      type: 'blank',
      correctWordId: blank.word.id,
    },
    disabled: !!filledWord, 
  });

  const colors = {
    default: '#adb5bd', 
    correct: '#92cc41', 
    wrong: '#e76e55', 
    hover: '#333', 
  };

  let borderColor = colors.default;
  let textColor = colors.default; 

  if (filledWord) {
    borderColor = colors.correct;
    textColor = colors.correct; 
  } else if (isWrong) {
    borderColor = colors.wrong;
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

    border: `2px solid ${borderColor}`,

    color: textColor,

    animation: isWrong ? 'shake 0.5s' : 'none',

    padding: 0,
    textAlign: 'center',
    fontWeight: 'bold',
    
    fontSize: 'inherit',
    
    lineHeight: 'calc(3.5rem - 4px)',
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