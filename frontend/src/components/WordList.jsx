// src/components/WordList.jsx
import PropTypes from 'prop-types';
// 1. (移除) createPortal 
// 2. (新) 导入 useDndContext 来检查拖拽状态
import { useDraggable, useDndContext } from '@dnd-kit/core'; 
import { useWordInteraction } from '../context/WordInteractionContext';

function DraggableWordButton({ word }) {
  const { setSelectedWord } = useWordInteraction();
  
  // 3. (移除) isDragging 不再需要
  const { attributes, listeners, setNodeRef, transform } =
    useDraggable({
      id: word.id,
    });

  // 4. (新) 检查这个按钮是否是当前被拖拽的那个
  const { active } = useDndContext();
  const isDragging = active && active.id === word.id;

  // 5. (修改) 
  //    - 宽度改为 'auto' (解决尺寸和偏移问题)
  //    - 移除 transform (DragOverlay 会处理)
  //    - 使用 'visibility' (解决消失问题)
  const style = {
    width: 'auto', 
    visibility: isDragging ? 'hidden' : 'visible', 
    zIndex: 'auto', // 移除了 zIndex 999
  };

  const button = (
    <button
      type="button"
      className="nes-btn"
      key={word.id}
      onClick={() => setSelectedWord(word)}
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
    >
      {word.maori_word}
    </button>
  );

  // 6. (改回) 不再使用 createPortal，总是正常渲染
  return button;
}

DraggableWordButton.propTypes = {
  word: PropTypes.shape({
    id: PropTypes.number.isRequired,
    maori_word: PropTypes.string.isRequired,
  }).isRequired,
};

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
        overflowX: 'hidden',
        padding: '0.5rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0.5rem',
        }}
      >
        {words.map((word) => (
          <DraggableWordButton
            key={word.id}
            word={word}
          />
        ))}
      </div>
    </div>
  );
}

WordList.propTypes = {
  words: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      maori_word: PropTypes.string.isRequired,
    })
  ).isRequired,
};

export default WordList;