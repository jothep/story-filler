// src/components/WordList.jsx (正确版本)
import React from 'react';
import { useDraggable } from '@dnd-kit/core';

//
// --- 👇 修复点 1：在这里接收 onWordSelect ---
//
function DraggableWordButton({ word, onWordSelect }) {
  
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: word.id,
  });

  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    zIndex: 99, 
  } : undefined;

  return (
    <button 
      type="button"
      className="nes-btn"
      key={word.id}
      //
      // --- 👇 修复点 2：现在 onWordSelect 是已定义的 ---
      //
      onClick={() => onWordSelect(word)} // <-- 这是你的报错行
      
      ref={setNodeRef} 
      style={{...style, flexGrow: 1}}
      {...listeners} 
      {...attributes} 
    >
      {word.maori_word}
    </button>
  );
}

//
// --- 👇 修复点 3：在这里也必须接收 onWordSelect ---
//
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
        padding: '0.5rem'
      }}
    >
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        
        {words.map(word => (
          //
          // --- 👇 修复点 4：把 onWordSelect 传递给子组件 ---
          //
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

export default WordList;