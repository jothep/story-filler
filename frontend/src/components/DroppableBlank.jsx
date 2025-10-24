// src/components/DroppableBlank.jsx
import React from 'react';
import { useDroppable } from '@dnd-kit/core';

// 1. 接收所有需要的 props
function DroppableBlank({ blank, uniqueId, filledWord, isWrong }) {

  const { isOver, setNodeRef } = useDroppable({
    id: uniqueId,
    data: {
      type: 'blank',
      correctWordId: blank.word.id,
    },
    disabled: !!filledWord, // 如果已填充，则禁用
  });

  // --- 2. 动态计算样式 (核心修复) ---
  
  // NES.css 调色板
  const colors = {
    default: '#adb5bd', // 默认灰色
    correct: '#92cc41', // 绿色 (is-success)
    wrong: '#e76e55',   // 红色 (is-error)
    hover: '#333'      // 拖拽悬停
  };
  
  let borderColor = colors.default;
  let textColor = colors.default; // 默认文字颜色

  if (filledWord) {
    // 答案正确 (绿色)
    borderColor = colors.correct;
    textColor = colors.correct; // 文字也用绿色
  } else if (isWrong) {
    // 答案错误 (红色)
    borderColor = colors.wrong;
  }

  // 这是我们组件的样式
  const style = {
    display: 'inline-block',
    margin: '0 0.25rem',
    minWidth: '100px', 
    height: '2.5rem', // 固定高度
    verticalAlign: 'middle',
    
    // 按你的要求：透明背景
    backgroundColor: isOver ? colors.hover : 'transparent', 
    
    borderRadius: '4px',
    boxSizing: 'border-box', // 确保 border 和 padding 包含在 height 内
    
    // 动态边框
    border: `2px solid ${borderColor}`,
    
    // 动态文字颜色
    color: textColor,

    // (可选) 错误时抖动
    animation: isWrong ? 'shake 0.5s' : 'none',
    
    // --- 样式修复：确保文字在框内居中 ---
    padding: 0, // 移除左右 padding
    textAlign: 'center',
    fontWeight: 'bold',
    fontSize: '0.9rem',
    // 关键修复: lineHeight 应该等于 框的内部高度
    // height (2.5rem) - 2 * border (2px)
    lineHeight: 'calc(2.5rem - 4px)',
  };
  // --- 👆 样式计算完毕 ---

  return (
    <span 
      ref={setNodeRef} 
      style={style}
    >
      {/*
      --- 3. 渲染内容 ---
      如果 'filledWord' 存在, 就显示它的毛利语单词
      */}
      {filledWord ? filledWord.maori_word : null}
    </span>
  );
}

export default DroppableBlank;