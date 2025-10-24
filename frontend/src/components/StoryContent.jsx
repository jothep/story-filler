// src/components/StoryContent.jsx
import React from 'react';

function StoryContent({ paragraphs }) {
  return (
    <div 
      className="nes-container is-dark" 
      style={{ height: '100%', boxSizing: 'border-box', overflowY: 'auto' }}
    >
      <button type="button" className="nes-btn is-primary" style={{ marginRight: '1rem' }}>
        play (all)
      </button>
      
      {/* 2. 遍历 'paragraphs' 数组 */}
      {paragraphs.map(para => (
        <div key={para.id} style={{ marginTop: '1rem' }}>
          <p>
            {/* 3. 显示每个段落的文本 */}
            {para.text}
          </p>
        </div>
      ))}
    </div>
  );
}

export default StoryContent;