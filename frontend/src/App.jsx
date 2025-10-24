// src/App.jsx

import React, { useState, useEffect } from 'react';
import './App.css';

import TopNav from './components/TopNav';
import StoryPicture from './components/StoryPicture';
import WordList from './components/WordList';
import StoryContent from './components/StoryContent';
import WordPic from './components/WordPic';
import WordAudio from './components/WordAudio';
import TriggerTips from './components/TriggerTips';

function App() {
    const [story, setStory] = useState(null); // 2. 创建 state
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
    //
    // 关键点 1: 这是你的开发 API 地址
    //
    //const API_URL = 'http://127.0.0.1:8080/api/stories/2/';
    const API_URL = '/api/stories/2/';

    fetch(API_URL)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        setStory(data); // 4. 存入 state
        setLoading(false);
      })
      .catch(err => {
        console.error("Fetch Error:", err);
        setError(err.message);
        setLoading(false);
      });

  }, []);
    if (loading) {
        return <div style={{ color: 'white', padding: '2rem' }}>Loading story...</div>;
    }
    if (error) {
    //
    // 关键点 2: 99% 的可能是 CORS 错误
    // 你必须在 Django 中配置 django-cors-headers
    // 允许 http://localhost:5173
    //
        return <div style={{ color: 'red', padding: '2rem' }}>Error loading story: {error}</div>;
    }

    return (
    // 这是我们的全屏“游戏窗口”
        <div className="game-screen">
      
      {/* 下面是你的7个布局区域。
        className 对应我们在 CSS 中定义的 "grid-area" 
      */}
      
      <div className="layout-nav">
        <TopNav />
      </div>

      <div className="layout-pic">
        <StoryPicture />
      </div>

      <div className="layout-list">
        {/* 7. 把 "word bank" 数据传递给 WordList */}
        <WordList words={story.words_in_bank} />
      </div>

      <div className="layout-text">
        {/* 8. 把 "paragraphs" 数据传递给 StoryContent */}
        <StoryContent paragraphs={story.paragraphs} />
      </div>

      <div className="layout-w-pic">
        <WordPic />
      </div>

      <div className="layout-w-audio">
        <WordAudio />
      </div>

      <div className="layout-tips">
        <TriggerTips />
      </div>

    </div>
  );
}

export default App;