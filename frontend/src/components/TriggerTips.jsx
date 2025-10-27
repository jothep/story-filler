// src/components/TriggerTips.jsx
import { useDroppable } from '@dnd-kit/core';
import { useWordInteraction } from '../context/WordInteractionContext';
import questionMarkIcon from '../assets/question_mark.png';

function TriggerTips() {
  const { selectedWord } = useWordInteraction();
  
  const { isOver, setNodeRef } = useDroppable({
    id: 'trigger-tips-droppable',
  });

  const style = {
    height: '100%',
    boxSizing: 'border-box',
    backgroundColor: isOver ? '#333' : undefined, 
    opacity: isOver ? 0.8 : 1.0,

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
