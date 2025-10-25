// src/Menu.jsx
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import Roll from './Roll'; 
import './Roll.css'; 
import { useStories } from './hooks/useStories';

// 为 Menu 添加一些简单的样式
const menuStyles = {
  position: 'relative', // 作为 Roll 的定位基准
  overflow: 'hidden',

  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '2rem',
  minHeight: '100vh',
  boxSizing: 'border-box', // 确保 padding 不会撑破屏幕
};

const titleContainerStyles = {
  width: '100%',
  maxWidth: '800px',
  marginBottom: '4rem', // 标题和菜单按钮之间的间距

  backgroundColor: 'rgba(255, 255, 255, 0.8)', // 白色、80%不透明度
  padding: '1rem',
  borderRadius: '4px',
};

const toggleContainerStyles = {
  position: 'absolute',
  top: '1.5rem',
  right: '1.5rem',
  zIndex: 10,
  color: 'white',
  textShadow: '1px 1px #000',
};

const menuListStyles = {
  display: 'flex',
  flexDirection: 'column',
  width: '100%',
  maxWidth: '400px', // 控制菜单按钮的宽度
  gap: '1.5rem', // 按钮之间的间距
};

function Menu() {
  const { stories, loading, error } = useStories();
  //const [stories, setStories] = useState([]);
  //const [loading, setLoading] = useState(true);
  //const [error, setError] = useState(null);

  const [isMusicPlaying, setIsMusicPlaying] = useState(true);
  const audioRef = useRef(null);

  useEffect(() => {
    // 2. (已修改) 直接使用你提供的后端 URL 路径
    const audio = new Audio('/media/bgm/Schumann_Fantasy.mp3');

    audio.loop = true;
    audio.volume = 0.3;
    audioRef.current = audio;

    if (isMusicPlaying) {
      audio.play().catch((e) => {
        console.warn('浏览器阻止了自动播放:', e);
        // setIsMusicPlaying(false);
      });
    }

    return () => {
      audio.pause();
      audioRef.current = null;
    };
  }, []); // 空依赖数组，这个 effect 只在组件加载时运行一次

  // ... (handleToggleMusic 函数保持不变) ...
  const handleToggleMusic = () => {
    const audio = audioRef.current;
    if (!audio) return;

    const newMusicState = !isMusicPlaying;
    setIsMusicPlaying(newMusicState);

    if (newMusicState) {
      audio.play();
    } else {
      audio.pause();
    }
  };

    /** 
  useEffect(() => {
  
    fetch('/api/stories/')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((data) => {
        setStories(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching stories:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []); */

  if (loading) {
    return <div style={{ padding: '2rem' }}>Loading stories...</div>;
  }

  if (error) {
    return (
      <div style={{ color: 'red', padding: '2rem' }}>
        Error loading stories: {error}
      </div>
    );
  }

  return (
    <div style={menuStyles}>
      <Roll /> {/* 更改 3: 使用 <Roll /> 组件 */}
      {/* BGM 开关 (保持不变) */}
      <div style={toggleContainerStyles}>
        <label>
          <input
            type="checkbox"
            className="nes-checkbox"
            checked={isMusicPlaying}
            onChange={handleToggleMusic}
          />
          <span>BGM</span>
        </label>
      </div>
      {/* 1. 标题 (如线框图所示) */}
      <div style={titleContainerStyles}>
        <div
          className="nes-container is-centered"
          style={{ backgroundColor: 'white' }}
        >
          <h1>Story Filler</h1>
        </div>
      </div>
      {/* 2. 故事列表 (如线框图所示) */}
      <div style={menuListStyles}>
        {stories.map((story) => (
          // AC 2: 点击导航到故事页面
          <Link
            key={story.id}
            to={`/story/${story.id}`} // 导航到 /story/1, /story/3 等
            className="nes-btn is-primary" // 使用 nes.css 按钮样式
          >
            {story.title}
          </Link>
        ))}
      </div>
    </div>
  );
}

export default Menu;
