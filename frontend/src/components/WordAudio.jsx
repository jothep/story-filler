// src/components/WordAudio.jsx
import PropTypes from 'prop-types';

// 1. 接收 'word' prop
function WordAudio({ word }) {
  
  // (可选) 播放音频的函数
  const playAudio = (audioSrc) => {
    if (audioSrc) {
      const audio = new Audio(audioSrc);
      audio.play();
    }
  };

  return (
    <div 
      className="nes-container is-dark" 
      style={{ 
        height: '100%', 
        boxSizing: 'border-box', 
        display: 'flex', 
        flexDirection: 'column', 
        justifyContent: 'space-around',
        padding: '0.5rem 1rem'
      }}
    >
      {/* 2. 条件渲染 */}
      {word ? (
        <>
          {/* 毛利语 */}
          <div 
            onClick={() => playAudio(word.maori_audio)} 
            style={{ cursor: 'pointer' }}
          >
            {/* 3. 使用 NES.css 的 'play' 图标 */}
            <i className="nes-icon play is-small" style={{ marginRight: '1rem' }}></i>
            <span>{word.maori_word}</span>
          </div>
          
          {/* 英语 */}
          <div 
            onClick={() => playAudio(word.english_audio)} 
            style={{ cursor: 'pointer' }}
          >
            <i className="nes-icon play is-small" style={{ marginRight: '1rem' }}></i>
            <span>{word.english_translation}</span>
          </div>
        </>
      ) : (
        <>
          {/* 3. 这是 'word' 为 null 时的占位符 */}
          <div>
            <button type="button" className="nes-btn is-disabled" style={{ marginRight: '1rem' }}>play</button>
            <span>maori word</span>
          </div>
          <div>
            <button type="button" className="nes-btn is-disabled" style={{ marginRight: '1rem' }}>play</button>
            <span>english word</span>
          </div>
        </>
      )}
    </div>
  );
}

WordAudio.propTypes = {
  word: PropTypes.shape({
    maori_word: PropTypes.string.isRequired,
    english_translation: PropTypes.string.isRequired,
    maori_audio: PropTypes.string,
    english_audio: PropTypes.string
  }) // 'word' 可以是 null
};

export default WordAudio;