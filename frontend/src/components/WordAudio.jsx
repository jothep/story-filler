// src/components/WordAudio.jsx
import React from 'react';

function WordAudio() {
  return (
    <div 
      className="nes-container is-dark" 
      style={{ 
        height: '100%', 
        boxSizing: 'border-box', 
        display: 'flex', 
        flexDirection: 'column', 
        justifyContent: 'space-around' // 让两个按钮上下分开点
      }}
    >
      <div>
        {/* 错误修正：这里应该是 type="button" */}
        <button type="button" className="nes-btn" style={{ marginRight: '1rem' }}>play</button>
        <span>maori word</span>
      </div>
      <div>
        <button type="button" className="nes-btn" style={{ marginRight: '1rem' }}>play</button>
        <span>english word</span>
      </div>
    </div>
  );
}

export default WordAudio;