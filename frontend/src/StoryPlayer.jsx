// src/App.jsx
import { DndContext } from '@dnd-kit/core';
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import './StoryPlayer.css';

//import TopNav from './components/TopNav';
import StoryPicture from './components/StoryPicture';
import WordList from './components/WordList';
import StoryContent from './components/StoryContent';
import WordPic from './components/WordPic';
import WordAudio from './components/WordAudio';
import TriggerTips from './components/TriggerTips';

function StoryPlayer() {
    const { storyId } = useParams();
    
    const [story, setStory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedWord, setSelectedWord] = useState(null);
    const [filledBlanks, setFilledBlanks] = useState({});

    const [wrongAttempt, setWrongAttempt] = useState(null);

    useEffect(() => {
    const API_URL = `/api/stories/${storyId}/`;

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
      });  }, [storyId]);

    function handleDragStart() {
        setWrongAttempt(null);
        }
    
    function handleDragEnd(event) {
        const { active, over } = event;

        if (!over || !active) return;

        const draggedWord = story.words_in_bank.find(
        (word) => word.id === active.id
    );

        if (!draggedWord) return;

        if (over.id === 'trigger-tips-droppable') {
        setSelectedWord(draggedWord);
        return; 
        }

    const dropZoneType = over.data.current?.type;
    if (dropZoneType === 'blank') {
      const uniqueBlankId = over.id; 
      const correctWordId = over.data.current.correctWordId;

      if (draggedWord.id === correctWordId) {
        setFilledBlanks(prevBlanks => ({
          ...prevBlanks,
          [uniqueBlankId]: draggedWord
        }));
        setWrongAttempt(null); 
      } else {
        console.log("Wrong answer.");
        setWrongAttempt(uniqueBlankId);
      }
    }
  }

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
          <Link to="/" className="nes-btn" style={{ margin: '1rem' }}>
            &lt;-- back to menu
          </Link>
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

export default StoryPlayer;