// src/pages/StoryPlayerUI.jsx
// Renders the main UI layout for the story player, composing all sub-components
// (like StoryContent, WordList, etc.). It consumes playback and interaction
// logic from contexts and specifically manages the `DragOverlay` display
// for dnd-kit by wrapping the context's drag handlers.
import { useState } from 'react';
import {
  DndContext,
  DragOverlay,
  TouchSensor,
  MouseSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { restrictToWindowEdges } from '@dnd-kit/modifiers';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';

import StoryPicture from '../components/StoryPicture';
import WordList from '../components/WordList';
import StoryContent from '../components/StoryContent';
import WordPic from '../components/WordPic';
import WordAudio from '../components/WordAudio';
import TriggerTips from '../components/TriggerTips';

import { useWordInteraction } from '../context/WordInteractionContext';
import { useStoryPlayback } from '../context/StoryPlaybackContext';

function WordOverlay({ word }) {
  return (
    <button type="button" className="nes-btn" style={{ width: 'auto' }}>
      {word.maori_word}
    </button>
  );
}

WordOverlay.propTypes = {
  word: PropTypes.shape({
    maori_word: PropTypes.string.isRequired,
  }).isRequired,
};

function StoryPlayerUI() {
  const {
    story,
    isMusicPlaying,
    handleToggleMusic,
    currentParagraph,
    currentParagraphIndex,
    handleNextParagraph,
    handlePrevParagraph,
    handlePlayParagraphAudio,
  } = useStoryPlayback();
  
  const { handleDragStart: originalDragStart, handleDragEnd: originalDragEnd } =
    useWordInteraction();

  const [activeWord, setActiveWord] = useState(null);

  // Configure sensors for both mouse and touch
  const mouseSensor = useSensor(MouseSensor, {
    activationConstraint: {
      distance: 5, // 5px movement before drag starts
    },
  });

  const touchSensor = useSensor(TouchSensor, {
    activationConstraint: {
      delay: 100, // 100ms press before drag starts (faster response)
      tolerance: 10, // 10px movement tolerance (more forgiving)
    },
  });

  const sensors = useSensors(mouseSensor, touchSensor);

  const handleDragStart = (event) => {
    document.body.classList.add('dragging');
    originalDragStart(event);
    const word = story.words_in_bank.find((w) => w.id === event.active.id);
    if (word) {
      setActiveWord(word);
      // Haptic feedback on touch devices
      if (window.navigator && window.navigator.vibrate) {
        window.navigator.vibrate(50);
      }
    }
  };


  const handleDragEnd = (event) => {
    document.body.classList.remove('dragging');
    originalDragEnd(event);
    setActiveWord(null);
  };

  const paragraphsExist = story.paragraphs && story.paragraphs.length > 0;

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      modifiers={[restrictToWindowEdges]}
    >
      <div className="game-screen">

        <div className="layout-nav"> 
          <div
            className="nes-container is-dark"
            style={{
              display: 'flex',
              alignItems: 'center',
              paddingTop: '0.5rem',
              paddingBottom: '0.5rem',
            }}
          >
            <Link
              to="/"
              style={{
                color: 'inherit',
                textDecoration: 'none',
                fontSize: '1rem',
                flexShrink: 0,
                padding: '0 0.5rem',
              }}
            >
              &lt;-- Menu
            </Link>
            <h1
              style={{
                flexGrow: 1,
                textAlign: 'center',
                fontSize: '2rem',
                margin: '0 1rem',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {story.title}
            </h1>
            {story.background_music_url && (
              <div style={{ flexShrink: 0 }}>
                <label>
                  <input
                    type="checkbox"
                    className="nes-checkbox is-dark"
                    checked={isMusicPlaying}
                    onChange={handleToggleMusic}
                  />
                  <span>BGM</span>
                </label>
              </div>
            )}
          </div>
        </div>

        <div className="layout-pic"> {/* */}
          <StoryPicture />
        </div>

        <div className="layout-list"> {/* */}
          <WordList words={story.words_in_bank} />
        </div>

        <div className="layout-text"> {/* */}
          {paragraphsExist ? (
            <StoryContent
              paragraph={currentParagraph}
              paragraphNumber={currentParagraphIndex + 1}
              totalParagraphs={story.paragraphs.length}
              onNext={handleNextParagraph}
              onPrev={handlePrevParagraph}
              onPlayAudio={handlePlayParagraphAudio}
            />
          ) : (
            <div className="nes-container is-dark" style={{ height: '100%', padding: '1rem' }}>
              <p>This story has no paragraphs yet.</p>
            </div>
          )}
        </div>

        <div className="layout-w-pic"> {/* */}
          <WordPic /> 
        </div>
        
        <div className="layout-w-audio"> {/* */}
          <WordAudio />
        </div>
        
        <div className="layout-tips"> {/* */}
          <TriggerTips /> 
        </div>

      </div>

      {activeWord && (
        <DragOverlay>
          <WordOverlay word={activeWord} />
        </DragOverlay>
      )}
    </DndContext>
  );
}

export default StoryPlayerUI;