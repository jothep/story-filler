// src/components/TriggerTips.jsx
import React from 'react';
// 1. 导入 useDroppable
import { useDroppable } from '@dnd-kit/core';

// 2. 接收从 App.jsx 传来的 selectedWord (可选)
function TriggerTips({ selectedWord }) {
  
  // 3. 设置 useDroppable，使用一个唯一的 ID
  const { isOver, setNodeRef } = useDroppable({
    id: 'trigger-tips-droppable',
  });

  // 4. (可选) 当有东西拖到上面时，改变样式
  const style = {
    height: '100%',
    boxSizing: 'border-box',
    backgroundColor: isOver ? '#333' : undefined, // 悬停时变暗
    opacity: isOver ? 0.8 : 1.0,
  };

  return (
    // 5. 应用 ref={setNodeRef} 和 style
    <div 
      ref={setNodeRef}
      className="nes-container is-dark" 
      style={style}
    >
      <p>Trigger tips</p>

      {/* 6. (可选) 显示拖拽到这里的结果 
        这会和点击 WordList 产生一样的效果
      */}
      {selectedWord && (
        <div style={{ marginTop: '1rem' }}>
          <p>Selected:</p>
          <p className="nes-text is-success">{selectedWord.maori_word}</p>
        </div>
      )}
    </div>
  );
}

export default TriggerTips;