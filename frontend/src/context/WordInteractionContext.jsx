// src/context/WordInteractionContext.jsx
// Manages all drag-and-drop interaction logic. This context tracks the
// `selectedWord` (for tips), `filledBlanks` (correctly placed words),
// and `wrongAttempt` state, providing handlers for dnd-kit events.
import { createContext, useState, useContext } from 'react';
import PropTypes from 'prop-types';

const WordInteractionContext = createContext();

export const useWordInteraction = () => {
  const context = useContext(WordInteractionContext);
  if (context === undefined) {
    throw new Error('useWordInteraction must be used within a WordInteractionProvider');
  }
  return context;
};

export function WordInteractionProvider({ children, wordsInBank }) {
  const [selectedWord, setSelectedWord] = useState(null);
  const [filledBlanks, setFilledBlanks] = useState({});
  const [wrongAttempt, setWrongAttempt] = useState(null);

  function handleDragStart() {
    setWrongAttempt(null); 
  }

  function handleDragEnd(event) {
    const { active, over } = event; 
    if (!over || !active) return; 

    const draggedWord = wordsInBank && wordsInBank.find(
      (word) => word.id === active.id
    ); 
    if (!draggedWord) return; 

    if (over.id === 'trigger-tips-droppable') {
      setSelectedWord(draggedWord); 
      return; 
    }

    const dropZoneType = over.data.current?.type;
    if (dropZoneType === 'blank') { 
      const uniqueBlankId = over.id; 
      const correctWordId = over.data.current.correctWordId; 

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