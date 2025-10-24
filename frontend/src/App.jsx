// src/App.jsx
import { DndContext } from '@dnd-kit/core';
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
    const [story, setStory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedWord, setSelectedWord] = useState(null);
    const [filledBlanks, setFilledBlanks] = useState({});

    const [wrongAttempt, setWrongAttempt] = useState(null);

    useEffect(() => {
    // 注意：你这里写的是 '3'。请确保这是你想要的故事 ID
    const API_URL = '/api/stories/3/';

    fetch(API_URL)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        setStory(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Fetch Error:", err);
        setError(err.message);
        setLoading(false);
      });  }, []);

    function handleDragStart() {
        setWrongAttempt(null);
        }
    
    // 这是 handleDragEnd 函数的唯一、正确版本
    function handleDragEnd(event) {
        const { active, over } = event;

        if (!over || !active) return;

        const draggedWord = story.words_in_bank.find(
        (word) => word.id === active.id
    );

        if (!draggedWord) return;

        // 逻辑 A：拖到了提示区
        if (over.id === 'trigger-tips-droppable') {
        setSelectedWord(draggedWord);
        return; 
        }

    // 逻辑 B：拖到了一个空白处
    const dropZoneType = over.data.current?.type;
    if (dropZoneType === 'blank') {
      const uniqueBlankId = over.id; 
      const correctWordId = over.data.current.correctWordId;

      if (draggedWord.id === correctWordId) {
        // 答案正确
        setFilledBlanks(prevBlanks => ({
          ...prevBlanks,
          [uniqueBlankId]: draggedWord
        }));
        setWrongAttempt(null); 
      } else {
        // 答案错误
        console.log("答案错误！");
        setWrongAttempt(uniqueBlankId);
      }
    }
  }
    // --- 这里是重复逻辑的开始，已被删除 ---

    if (loading) {
        return <div style={{ color: 'white', padding: '2rem' }}>Loading story...</div>;
    }
    if (error) {
        return <div style={{ color: 'red', padding: '2rem' }}>Error loading story: {error}</div>;
    }
    if (!story) { return <div>No story found.</div>; }

    return (
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="game-screen">
        
        <div className="layout-nav">
          <TopNav />
        </div>

        <div className="layout-pic">
          <StoryPicture />
        </div>
        
        <div className="layout-list">
          <WordList 
            words={story.words_in_bank} 
            onWordSelect={setSelectedWord}
          />
        </div>

        <div className="layout-text">
          <StoryContent 
            paragraphs={story.paragraphs} 
            filledBlanks={filledBlanks}
            wrongAttempt={wrongAttempt} 
          />
        </div>
        
        <div className="layout-w-pic">
          <WordPic word={selectedWord} />
        </div>
        <div className="layout-w-audio">
          <WordAudio word={selectedWord} />
        </div>
        <div className="layout-tips">
          <TriggerTips selectedWord={selectedWord} />
        </div>

      </div>
    </DndContext> );
}

export default App;