// src/components/TriggerTips.jsx
// Implements the "Drag word here" drop zone using `dnd-kit`.
// When a word is dropped, it updates the `selectedWord` in the
// `WordInteractionContext`.

import { useDroppable, useDndContext } from '@dnd-kit/core';
import { useWordInteraction } from '../context/WordInteractionContext';
import questionMarkIcon from '../assets/question_mark.png';

function TriggerTips() {
  const { selectedWord } = useWordInteraction();
  const { active } = useDndContext(); // Detect if anything is being dragged

  const { isOver, setNodeRef } = useDroppable({
    id: 'trigger-tips-droppable',
  });

  const isDragging = !!active; // True if any word is being dragged

  const style = {
    height: '100%',
    boxSizing: 'border-box',
    backgroundColor: isOver ? '#333' : undefined,
    opacity: isOver ? 0.8 : 1.0,
    border: isDragging ? '3px dashed #ffd700' : undefined, // Yellow dashed border when dragging
    boxShadow: isDragging ? '0 0 15px rgba(255, 215, 0, 0.5)' : undefined, // Yellow glow

    backgroundImage: `url(${questionMarkIcon})`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'center center',
    backgroundSize: 'contain',

    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'flex-start',

    padding: '0.5rem',
    paddingTop: '0.5rem',

    transition: 'all 0.3s ease', // Smooth transitions
    animation: isDragging ? 'pulse-glow 1.5s ease-in-out infinite' : 'none', // Pulse animation
  };

  const textContainerStyle = {
    flexShrink: 0,
    textAlign: 'center',
    minHeight: '2rem', 
  };


  return (
    <div ref={setNodeRef} className="nes-container is-dark" style={style}>
      
      <div style={textContainerStyle}>
        {selectedWord ? (
          
          <p>
            <span className="nes-text is-success">Selected:{selectedWord.maori_word}</span>
          </p>

        ) : (

          <p className="nes-text is-warning">
            Drag word here
          </p>
          
        )}
      </div>
    </div>
  );
}

export default TriggerTips;
