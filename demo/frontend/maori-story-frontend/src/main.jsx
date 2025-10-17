import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';

// Django API的地址
const API_URL = 'http://127.0.0.1:8000/api/stories/';

// --- 纯净的React应用组件 ---
function App() {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStories = async () => {
      try {
        const response = await fetch(API_URL);
        if (!response.ok) {
          throw new Error(`HTTP Error! Status: ${response.status}`);
        }
        const data = await response.json();
        setStories(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchStories();
  }, []);

  // --- 渲染逻辑 ---
  if (loading) {
    return <h1>正在加载故事...</h1>;
  }

  if (error) {
    return <h1 style={{ color: 'red' }}>加载错误: {error}</h1>;
  }

  return (
    <div>
      <header style={{ backgroundColor: '#282c34', padding: '20px', color: 'white', textAlign: 'center' }}>
        <h1>Māori Story-Fill (纯净测试版)</h1>
      </header>
      <main style={{ padding: '20px' }}>
        {stories.length > 0 ? (
          <ul>
            {stories.map(story => (
              <li key={story.id} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
                <h2>{story.title}</h2>
              </li>
            ))}
          </ul>
        ) : (
          <p>没有找到故事。请检查Django后台是否已添加内容。</p>
        )}
      </main>
    </div>
  );
}

// --- 渲染应用 ---
const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);