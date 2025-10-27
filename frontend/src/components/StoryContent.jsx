// src/components/StoryContent.jsx
import DroppableBlank from './DroppableBlank';
import { useWordInteraction } from '../context/WordInteractionContext';
import { useStoryPlayback } from '../context/StoryPlaybackContext';

function parseText(text) {
  const regex = /(__BLANK_[a-zA-Z0-9_]+__)/g;
  return text.split(regex).filter((part) => part.length > 0);
}

function StoryContent() {

  const { filledBlanks, wrongAttempt } = useWordInteraction();
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
        
        {paragraphNumber > 1 && (
          <button
            type="button"
            className="nes-btn"
            onClick={onPrev}
          >
            &lt; Prev
          </button>
        )}

        {paragraphNumber < totalParagraphs && (
          <button
            type="button"
            className="nes-btn"
            onClick={onNext}
            style={{ marginLeft: 'auto' }} 
          >
            Next &gt;
          </button>
        )}
      </div>

    </div>
  );
}

export default StoryContent;