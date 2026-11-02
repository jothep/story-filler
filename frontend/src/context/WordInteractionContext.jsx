import { createContext, useState, useContext } from 'react';
import PropTypes from 'prop-types';

const WordInteractionContext = createContext(
  /** @type {import('../types').WordInteractionState|undefined} */ (undefined)
);

export const useWordInteraction = () => {
  const context = useContext(WordInteractionContext);
  if (context === undefined) {
    throw new Error(
      'useWordInteraction must be used within a WordInteractionProvider'
    );
  }
  return context;
};

/**
 * @param {{children: import('react').ReactNode, wordsInBank?: import('../types').Word[]}} props
 */
export function WordInteractionProvider({ children, wordsInBank }) {
  const [selectedWord, setSelectedWord] = useState(
    /** @type {import('../types').Word|null} */ (null)
  );
  const [filledBlanks, setFilledBlanks] = useState(
    /** @type {Record<string, import('../types').Word>} */ ({})
  );
  const [wrongAttempt, setWrongAttempt] = useState(
    /** @type {import('@dnd-kit/core').UniqueIdentifier|null} */ (null)
  );

  function handleDragStart() {
    setWrongAttempt(null);
  }

  /** @param {import('@dnd-kit/core').DragEndEvent} event */
  function handleDragEnd(event) {
    const { active, over } = event;
    if (!over || !active) return;

    const draggedWord =
      wordsInBank && wordsInBank.find((word) => word.id === active.id);
    if (!draggedWord) return;

    if (over.id === 'trigger-tips-droppable') {
      setSelectedWord(draggedWord);
      return;
    }

    const dropZone = over.data.current;
    if (dropZone?.type === 'blank') {
      const uniqueBlankId = over.id;
      const correctWordId = dropZone.correctWordId;

      if (draggedWord.id === correctWordId) {
        setFilledBlanks((prevBlanks) => ({
          ...prevBlanks,
          [uniqueBlankId]: draggedWord,
        }));
        setWrongAttempt(null);
      } else {
        setWrongAttempt(uniqueBlankId);
      }
    }
  }

  const value = {
    selectedWord,
    setSelectedWord,
    filledBlanks,
    wrongAttempt,
    handleDragStart,
    handleDragEnd,
  };

  return (
    <WordInteractionContext.Provider value={value}>
      {children}
    </WordInteractionContext.Provider>
  );
}

WordInteractionProvider.propTypes = {
  wordsInBank: PropTypes.array,
  children: PropTypes.node.isRequired,
};

WordInteractionProvider.defaultProps = {
  wordsInBank: [],
};
