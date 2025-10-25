// src/components/StoryContent.jsx
import React from 'react'; // React 必须在作用域内
import PropTypes from 'prop-types';
import DroppableBlank from './DroppableBlank'; // 1. 保留了你对 DroppableBlank 的导入

// 2. 保留了你原有的、有意义的 parseText 辅助函数
function parseText(text) {
  const regex = /(__BLANK_[a-zA-Z0-9_]+__)/g;
  return text.split(regex).filter((part) => part.length > 0);
}

// ---------------------------------------------------------
// 主组件：StoryContent (已整合)
// ---------------------------------------------------------
function StoryContent({
  // 3. 使用了新的 props
  paragraph,
  paragraphNumber,
  totalParagraphs,
  onNext,
  onPrev,
  onPlayAudio,
  // 4. 保留了你原有的 props
  filledBlanks,
  wrongAttempt,
}) {

  // 5. 保留了你原有的、有意义的 renderParagraph 逻辑
  const renderParagraph = (para) => {
    // (安全检查) 确保 para 存在，并且 text 存在
    if (!para || !para.text) {
      return null;
    }
    
    const parts = parseText(para.text);

    return parts.map((part, index) => {
      if (part.startsWith('__BLANK_')) {
        
        // (安全检查) 确保 blank_links 存在
        if (!para.blank_links) return <span key={`missing-span-${index}`}>{part}</span>;

        const blankData = para.blank_links.find((b) => b.placeholder === part);

        if (blankData) {
          const uniqueId = `blank-${blankData.id}-${index}`;
          const filledWord = filledBlanks[uniqueId];
          const isWrong = wrongAttempt === uniqueId;

          return (
            <DroppableBlank
              key={uniqueId}
              uniqueId={uniqueId}
              blank={blankData}
              filledWord={filledWord}
              isWrong={isWrong}
            />
          );
        }
        return <span key={`missing-span-${index}`}>{part}</span>;
      }
      return <span key={`span-${index}`}>{part}</span>;
    });
  };

  // 6. (已修改) 容器样式，使其能容纳顶部和底部栏
  const containerStyle = {
    height: '100%',
    width: '100%',
    display: 'flex',
    flexDirection: 'column', // 垂直布局
    padding: '1rem',
  };

  // 顶部栏
  const topBarStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
    borderBottom: '2px solid #555',
    paddingBottom: '0.5rem',
  };

  // 底部导航栏
  const navStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    marginTop: 'auto', // (关键) 把导航推到底部
    paddingTop: '0.5rem',
    borderTop: '2px solid #555',
  };

  // (安全检查) 如果 paragraph 意外为 null，不渲染
  if (!paragraph) {
    return (
      <div
        className="nes-container is-dark"
        style={{ height: '100%', padding: '1rem' }}
      >
        <p>Loading paragraph...</p>
      </div>
    );
  }

  // 7. (已修改) 这是新的 return 布局
  return (
    <div className="nes-container is-dark with-title" style={containerStyle}>
      {/* 1. 顶部栏 (新功能) */}
      <div style={topBarStyle}>
        <button
          type="button"
          className="nes-btn is-primary"
          onClick={() => onPlayAudio(paragraph.audio)}
          disabled={!paragraph.audio}
        >
          reading
        </button>
        <span style={{ fontSize: '1rem' }}>
          Paragraph {paragraphNumber} / {totalParagraphs}
        </span>
      </div>

      {/* 2. 故事文本内容 (使用你原有的渲染逻辑) */}
      <div style={{ overflowY: 'auto', lineHeight: '2.5rem', marginTop: '1rem' }}>
        <p>
          {/* 这里是关键：我们调用你保留的 renderParagraph 函数 */}
          {renderParagraph(paragraph)}
        </p>
      </div>

      {/* 3. 底部导航 (新功能) */}
      <div style={navStyle}>
        <button
          type="button"
          className="nes-btn"
          onClick={onPrev}
          disabled={paragraphNumber <= 1}
        >
          &lt; Prev
        </button>
        <button
          type="button"
          className="nes-btn"
          onClick={onNext}
          disabled={paragraphNumber >= totalParagraphs}
        >
          Next &gt;
        </button>
      </div>
    </div>
  );
}

// 8. (已修改) 更新 PropTypes 以匹配新 props
StoryContent.propTypes = {
  paragraph: PropTypes.shape({ // 之前是 'paragraphs' 数组
    id: PropTypes.number.isRequired,
    text: PropTypes.string.isRequired,
    audio: PropTypes.string, // 音频 URL
    blank_links: PropTypes.arrayOf(PropTypes.object), // blank_links 可以为 null 或 undefined
  }),
  paragraphNumber: PropTypes.number.isRequired,
  totalParagraphs: PropTypes.number.isRequired,
  onNext: PropTypes.func.isRequired,
  onPrev: PropTypes.func.isRequired,
  onPlayAudio: PropTypes.func.isRequired,
  filledBlanks: PropTypes.object.isRequired,
  wrongAttempt: PropTypes.string,
};

export default StoryContent;