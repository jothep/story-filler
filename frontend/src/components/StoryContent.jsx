// src/components/StoryContent.jsx
import DroppableBlank from './DroppableBlank';
import { useWordInteraction } from '../context/WordInteractionContext';
import { useStoryPlayback } from '../context/StoryPlaybackContext';

import { useNavigate, useParams } from 'react-router-dom';
import { useMemo } from 'react';

function parseText(text) {
  const regex = /(__BLANK_[a-zA-Z0-9_]+__)/g;
  return text.split(regex).filter((part) => part.length > 0);
}

function StoryContent() {

  const navigate = useNavigate();
  const { storyId } = useParams();

  const { filledBlanks } = useWordInteraction();
  const {
    currentParagraph,
    currentParagraphIndex,
    handleNextParagraph,
    handlePrevParagraph,
    handlePlayParagraphAudio,
    story, 
  } = useStoryPlayback();

    const paragraph = currentParagraph;
    const paragraphNumber = currentParagraphIndex + 1;
    const totalParagraphs = story.paragraphs.length;
    const onNext = handleNextParagraph;
    const onPrev = handlePrevParagraph;
    const onPlayAudio = handlePlayParagraphAudio;

  const totalBlanksInStory = useMemo(() => {
    if (!story || !story.paragraphs) return 0;
    return story.paragraphs.reduce((count, p) => {
      return count + (p.blank_links ? p.blank_links.length : 0);
    }, 0);
  }, [story]);

  const filledBlanksCount = Object.keys(filledBlanks).length;
  const isStoryComplete = totalBlanksInStory > 0 && filledBlanksCount === totalBlanksInStory;
  const isLastPage = paragraphNumber >= totalParagraphs;

  const handleCompleteClick = () => {
    navigate(`/story/${storyId}/complete`);
  };

  const renderParagraph = (para) => {
    if (!para || !para.text) {
      return null;
    }
    const parts = parseText(para.text);
    return parts.map((part, index) => {
      if (part.startsWith('__BLANK_')) {
        
        if (!para.blank_links) return <span key={`missing-span-${index}`}>{part}</span>;

        const blankData = para.blank_links.find((b) => b.placeholder === part);

        if (blankData) {
          const { wrongAttempt } = useWordInteraction.getState ? useWordInteraction.getState() : useWordInteraction();
          const uniqueId = `blank-${blankData.id}-${index}`;
          const filledWord = filledBlanks[uniqueId];
          const isWrong = wrongAttempt === uniqueId;

          return (
            <DroppableBlank
              key={uniqueId}
              uniqueId={uniqueId}
              blank={blankData}
              filledWord={filledWord}
              isWrong={isWrong}
            />
          );
        }
        return <span key={`missing-span-${index}`}>{part}</span>;
      }
      return <span key={`span-${index}`}>{part}</span>;
    });
  };

  const containerStyle = {
    height: '100%',
    width: '100%',
    display: 'flex',
    flexDirection: 'column', 
    padding: '1rem',
  };

  const topBarStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
    borderBottom: '2px solid #555',
    paddingBottom: '0.5rem',
  };

  const navStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 'auto', 
    paddingTop: '0.5rem',
    borderTop: '2px solid #555',
  };

  if (!paragraph) {
    return (
      <div
        className="nes-container is-dark"
        style={{ height: '100%', padding: '1rem' }}
      >
        <p>Loading paragraph...</p>
      </div>
    );
  }

  return (
    <div className="nes-container is-dark with-title" style={containerStyle}>
      <div style={topBarStyle}>
        <button
          type="button"
          className="nes-btn is-primary"
          onClick={() => onPlayAudio(paragraph.audio)}
          disabled={!paragraph.audio}
        >
          reading
        </button>
        <span style={{ fontSize: '1rem' }}>
          Paragraph {paragraphNumber} / {totalParagraphs}
        </span>
      </div>

      <div
        style={{
          overflowY: 'auto',
          marginTop: '1rem',
          fontSize: '2rem',
          lineHeight: '1.5',
        }}
      >
        <p>
          {renderParagraph(paragraph)}
        </p>
      </div>

      <div style={navStyle}>
        
        <button
          type="button"
          className="nes-btn"
          onClick={onPrev}
          style={{ visibility: paragraphNumber > 1 ? 'visible' : 'hidden' }}
        >
          &lt; Prev
        </button>
        
        {isStoryComplete && (
          <button
            type="button"
            className="nes-btn is-success"
            onClick={handleCompleteClick}
          >
            Complete Story!
          </button>
        )}

        <button
          type="button"
          className="nes-btn"
          onClick={onNext}
          style={{ visibility: paragraphNumber < totalParagraphs ? 'visible' : 'hidden' }}
        >
          Next &gt;
        </button>
      </div>

    </div>
  );
}

export default StoryContent;