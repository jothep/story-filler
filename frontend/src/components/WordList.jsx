// src/components/WordList.jsx 

import React from 'react';

// 👇 关键修复：
// 使用 { words } 来直接“解包”从 App.jsx 传来的 'words' prop
function WordList({ words }) { 

  // (可选) 添加一个安全检查，防止 words 意外为 null
  if (!words) {
    return <div>Loading words...</div>;
  }

  return (
    <div 
      className="nes-container is-dark" 
      style={{ height: '100%', boxSizing: 'border-box', overflowY: 'auto' }}
    >
      <ul className="nes-list is-disc">
        {/* 👇 现在 'words' 变量是明确定义的，可以安全使用 .map */}
        {words.map(word => (
          <li key={word.id}>
            {word.maori_word}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default WordList;