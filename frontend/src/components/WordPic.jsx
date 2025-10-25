// src/components/WordPic.jsx
import PropTypes from 'prop-types';

function WordPic({ word }) {
  // 1. (已修改) 容器的样式
  const containerStyle = {
    height: '100%',
    width: '100%', // (新增) 明确设置宽度为 100%
    boxSizing: 'border-box',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0.5rem',
    overflow: 'hidden', // (新增) 关键！防止子元素撑开容器
  };

  // 2. (已修改) 图片的样式
  const imageStyle = {
    width: '100%', // (修改) 从 maxWidth 改为 width
    height: '100%', // (修改) 从 maxHeight 改为 height
    objectFit: 'contain', // (保留) 确保图片完整显示
  };

  return (
    <div
      className="nes-container is-dark"
      style={containerStyle} // 3. 应用容器样式
    >
      {word ? (
        <img
          src={word.image}
          alt={word.english_translation}
          style={imageStyle} // 4. 应用图片样式
        />
      ) : (
        <p>word pic</p>
      )}
    </div>
  );
}

WordPic.propTypes = {
  word: PropTypes.shape({
    image: PropTypes.string,
    english_translation: PropTypes.string.isRequired,
  }),
};

export default WordPic;