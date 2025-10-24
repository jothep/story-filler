// src/components/WordPic.jsx
import React from 'react';

// 1. 接收 'word' prop
function WordPic({ word }) {
  return (
    <div 
      className="nes-container is-dark" 
      style={{ 
        height: '100%', 
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0.5rem' // 避免图片贴边
      }}
    >
      {/* 2. 条件渲染：
          - 如果 'word' 存在 (被点击了)，显示图片
          - 否则，显示占位符
      */}
      {word ? (
        <img 
          // 3. 'word.image' 已经是我们修复后的相对路径
          // 例如: "/media/word_images/water.png"
          src={word.image} 
          alt={word.english_translation}
          style={{ 
            maxWidth: '100%', 
            maxHeight: '100%', 
            objectFit: 'contain' // 确保图片完整显示
          }}
        />
      ) : (
        <p>word pic</p> // 占位符
      )}
    </div>
  );
}

export default WordPic;