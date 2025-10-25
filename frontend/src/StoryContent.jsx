// src/StoryContent.jsx
import React from 'react';
import { useDroppable } from '@dnd-kit/core';

// ---------------------------------------------------------
// 内部组件：用于渲染单个可拖放的空白区域
// ---------------------------------------------------------
function BlankDroppable({ uniqueBlankId, correctWordId, filledWord, isWrong }) {
  const { setNodeRef, isOver } = useDroppable({
    id: uniqueBlankId,
    data: {
      type: 'blank',
      correctWordId: correctWordId,
    },
  });

  const style = {
    display: 'inline-block',
    padding: '0.2rem 0.5rem',
    border: '2px dashed #888',
    borderRadius: '4px',
    minWidth: '100px',
    textAlign: 'center',
    verticalAlign: 'middle',
    color: 'white',
    backgroundColor: isOver ? '#555' : 'transparent',
    animation: isWrong ? 'shake 0.5s' : 'none',
    borderColor: isWrong ? '#e76e55' : '#888',
  };

  return (
    <span ref={setNodeRef} style={style}>
      {filledWord ? filledWord.maori_word : '...'}
    </span>
  );
}

// ---------------------------------------------------------
// 内部组件：用于解析文本并插入空白区域
// ---------------------------------------------------------
function ParagraphTextRenderer({ paragraph, filledBlanks, wrongAttempt }) {
  // (重要!!)
  // 这就是修复你崩溃问题的安全检查
  // 如果 paragraph 为 null，或者 text 不存在，或者 blank_links 不存在
  // 它会安全地退出，而不是试图去 .map() 一个 undefined。
  if (!paragraph || !paragraph.text || !paragraph.blank_links) {
    return <p>{paragraph ? paragraph.text : '...'}</p>;
  }

  // 1. 创建正则表达式
  const placeholders = paragraph.blank_links.map((link) =>
    link.placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  );

  // (安全检查) 如果没有 placeholders，不要创建空的 RegExp
  if (placeholders.length === 0) {
    return <p>{paragraph.text}</p>;
  }

  const regex = new RegExp(`(${placeholders.join('|')})`, 'g');

  // 2. 分割文本
  const parts = paragraph.text.split(regex);

  // 3. 渲染文本和空白
  return (
    <p style={{ lineHeight: '2.5', fontSize: '1rem' }}>
      {parts.map((part, index) => {
        const matchingLink = paragraph.blank_links.find(
          (link) => link.placeholder === part
        );

        if (matchingLink) {
          // 这是一个空白
          const uniqueBlankId = `p${paragraph.id}-b${matchingLink.id}`;
          const filledWord = filledBlanks[uniqueBlankId];
          const isWrong = wrongAttempt === uniqueBlankId;

          return (
            <BlankDroppable
              key={index}
              uniqueBlankId={uniqueBlankId}
              correctWordId={matchingLink.word.id}
              filledWord={filledWord}
              isWrong={isWrong}
            />
          );
        } else {
          // 这是普通文本
          return <span key={index}>{part}</span>;
        }
      })}
    </p>
  );
}

// ---------------------------------------------------------
// 主组件：StoryContent
// ---------------------------------------------------------
function StoryContent({
  paragraph,
  paragraphNumber,
  totalParagraphs,
  onNext,
  onPrev,
  onPlayAudio,
  filledBlanks,
  wrongAttempt,
}) {
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
    marginTop: 'auto',
    paddingTop: '0.5rem',
    borderTop: '2px solid #555',
  };

  // 容器
  const containerStyle = {
    height: '100%',
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    padding: '1rem',
  };

  return (
    <div className="nes-container is-dark with-title" style={containerStyle}>
      {/* 1. 顶部栏 */}
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

      {/* 2. 故事文本内容 */}
      <div style={{ overflowY: 'auto' }}>
        <ParagraphTextRenderer
          paragraph={paragraph}
          filledBlanks={filledBlanks}
          wrongAttempt={wrongAttempt}
        />
      </div>

      {/* 3. 底部导航 */}
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

export default StoryContent;
