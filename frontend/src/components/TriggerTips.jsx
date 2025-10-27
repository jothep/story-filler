// src/components/TriggerTips.jsx
import PropTypes from 'prop-types';
import { useDroppable } from '@dnd-kit/core';
import { useWordInteraction } from '../context/WordInteractionContext';
import questionMarkIcon from '../assets/question_mark.png';

function TriggerTips() {
  const { selectedWord } = useWordInteraction();
  
  const { isOver, setNodeRef } = useDroppable({
    id: 'trigger-tips-droppable',
  });

  // 4. (可选) 当有东西拖到上面时，改变样式
  const style = {
    height: '100%',
    boxSizing: 'border-box',
    backgroundColor: isOver ? '#333' : undefined, // 悬停时变暗
    opacity: isOver ? 0.8 : 1.0,

    backgroundImage: `url(${questionMarkIcon})`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'center center',
    backgroundSize: 'contain', // 确保图片完整显示
    
    // --- 修改 flex 布局以将文本推到底部 ---
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'flex-start', // <--- 改为 'flex-end' (推到底部)
    
    // (已修改) 为底部的文字留出空间
    padding: '0.5rem',
    paddingTop: '0.5rem',
  };

  /* const imageStyle = {
    width: '100%',
    height: 'auto',
    objectFit: 'contain',
    maxHeight: '128px', // (可选) 限制图片最大高度
    // flexGrow: 1, 
  }; */

  const textContainerStyle = {
    flexShrink: 0,
    textAlign: 'center',
    minHeight: '2rem', 
  };


  return (
    // 5. 应用 ref={setNodeRef} 和 style
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

TriggerTips.propTypes = {

};

export default TriggerTips;
