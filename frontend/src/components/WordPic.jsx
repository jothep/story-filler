// src/components/WordPic.jsx
import PropTypes from 'prop-types';
// (已修复) 1. 导入 Hook
import { useWordInteraction } from '../context/WordInteractionContext';

// (已修复) 2. 移除 'word' prop
function WordPic() {
  // (已修复) 3. 从 Hook 中获取 'selectedWord'
  const { selectedWord } = useWordInteraction();

  // 您的样式 (保持不变)
  const containerStyle = {
    height: '100%',
    width: '100%',
    boxSizing: 'border-box',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0.5rem',
    overflow: 'hidden',
  }; //

  const imageStyle = {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
  }; //

  return (
    <div
      className="nes-container is-dark"
      style={containerStyle} //
    >
      {/* (已修复) 4. 将所有 'word' 替换为 'selectedWord' */}
      {selectedWord ? (
        <img
          src={selectedWord.image} //
          alt={selectedWord.english_translation} //
          style={imageStyle} //
        />
      ) : (
        <p>word pic</p> //
      )}
    </div>
  );
}

// (已修复) 5. 移除 PropTypes，因为不再接收 props
WordPic.propTypes = {
  // word: PropTypes.shape({ ... }),
}; //

export default WordPic;