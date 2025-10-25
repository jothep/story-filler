// src/components/StoryContent.jsx
import PropTypes from 'prop-types';
import DroppableBlank from './DroppableBlank'; // 导入新组件

// 辅助函数 (不变)
function parseText(text) {
  const regex = /(__BLANK_[a-zA-Z0-9_]+__)/g;
  return text.split(regex).filter((part) => part.length > 0);
}

function StoryContent({ paragraphs, filledBlanks, wrongAttempt }) {
  const renderParagraph = (para) => {
    const parts = parseText(para.text);

    return parts.map((part, index) => {
      if (part.startsWith('__BLANK_')) {
        const blankData = para.blank_links.find((b) => b.placeholder === part);

        if (blankData) {
          const uniqueId = `blank-${blankData.id}-${index}`;
          const filledWord = filledBlanks[uniqueId];

          // --- 👇 2. 检查这个 blank 是否是刚发生错误的那个 ---
          const isWrong = wrongAttempt === uniqueId;

          return (
            <DroppableBlank
              key={uniqueId}
              uniqueId={uniqueId}
              blank={blankData}
              filledWord={filledWord}
              // --- 👇 3. 传递 'isWrong' prop ---
              isWrong={isWrong}
            />
          );
        }
        return <span key={`missing-span-${index}`}>{part}</span>;
      }
      return <span key={`span-${index}`}>{part}</span>;
    });
  };

  return (
    <div
      className="nes-container is-dark"
      style={{ height: '100%', boxSizing: 'border-box', overflowY: 'auto' }}
    >
      <button
        type="button"
        className="nes-btn is-primary"
        style={{ marginRight: '1rem' }}
      >
        play (all)
      </button>

      {paragraphs.map((para) => (
        // (这个 key={para.id} 是正确的，不需要改)
        <div key={para.id} style={{ marginTop: '1rem', lineHeight: '2.5rem' }}>
          <p>{renderParagraph(para)}</p>
        </div>
      ))}
    </div>
  );
}

StoryContent.propTypes = {
  paragraphs: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      text: PropTypes.string.isRequired,
      blank_links: PropTypes.arrayOf(PropTypes.object).isRequired,
    })
  ).isRequired,
  filledBlanks: PropTypes.object.isRequired,
  wrongAttempt: PropTypes.string, // 'wrongAttempt' 可以是 null
};

export default StoryContent;
