// src/Menu.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

// 为 Menu 添加一些简单的样式
const menuStyles = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '2rem',
  minHeight: '100vh',
  boxSizing: 'border-box' // 确保 padding 不会撑破屏幕
};

const titleContainerStyles = {
  width: '100%',
  maxWidth: '800px',
  marginBottom: '4rem', // 标题和菜单按钮之间的间距
};

const menuListStyles = {
  display: 'flex',
  flexDirection: 'column',
  width: '100%',
  maxWidth: '400px', // 控制菜单按钮的宽度
  gap: '1.5rem' // 按钮之间的间距
};

function Menu() {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 使用你提供的 API 端点
    fetch('/api/stories/')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        setStories(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching stories:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div style={{ padding: '2rem' }}>Loading stories...</div>;
  }

  if (error) {
    return <div style={{ color: 'red', padding: '2rem' }}>Error loading stories: {error}</div>;
  }

  return (
    <div style={menuStyles}>
      
      {/* 1. 标题 (如线框图所示) */}
      <div style={titleContainerStyles}>
        <div className="nes-container is-centered">
          <h1>Maori Story Fill</h1>
        </div>
      </div>

      {/* 2. 故事列表 (如线框图所示) */}
      <div style={menuListStyles}>
        {stories.map(story => (
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