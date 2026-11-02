// src/components/StoryContent.jsx
// Renders the main story text, parsing it to replace placeholders with
// `DroppableBlank` components. It manages paragraph navigation (Prev/Next),
// handles paragraph audio, and calculates when the story is complete
// to display the "Complete Story!" button.
import DroppableBlank from './DroppableBlank';
import { useWordInteraction } from '../context/WordInteractionContext';
import { useStoryPlayback } from '../context/StoryPlaybackContext';

import { useNavigate, useParams } from 'react-router-dom';
import { useMemo } from 'react';

// Use the same parsed blanks for rendering and completion checks. A missing
// association remains visible, but can never be counted as a completed answer.
function parseParagraph(paragraph) {
  const parts = (paragraph.text || '').split(/(__BLANK_[a-zA-Z0-9_]+__)/g);
  return parts.filter(Boolean).map((text, index) => {
    if (!/^__BLANK_[a-zA-Z0-9_]+__$/.test(text)) return { text };

    const blank = paragraph.blank_links?.find(
      (link) => link.placeholder === text
    ) || { word: null };
    const uniqueId =
      blank.id != null
        ? `blank-${blank.id}-${index}`
        : `missing-${paragraph.id}-${index}`;
    return { blank, uniqueId };
  });
}

function StoryContent() {
  const { filledBlanks, wrongAttempt } = useWordInteraction();
  const navigate = useNavigate();
  const { storyId } = useParams();
  const {
    currentParagraph: paragraph,
    currentParagraphIndex,
    handleNextParagraph: onNext,
    handlePrevParagraph: onPrev,
    handlePlayParagraphAudio: onPlayAudio,
    story,
  } = useStoryPlayback();

  const paragraphNumber = currentParagraphIndex + 1;
  const totalParagraphs = story.paragraphs.length;
  const parsedParagraphs = useMemo(
    () => story.paragraphs.map(parseParagraph),
    [story.paragraphs]
  );
  const allBlanks = parsedParagraphs.flat().filter((part) => part.blank);
  const hasUnavailableWords = allBlanks.some(
    ({ blank }) => blank.word?.id == null
  );
  const isStoryComplete =
    allBlanks.length > 0 &&
    allBlanks.every(
      ({ blank, uniqueId }) =>
        blank.word?.id != null && filledBlanks[uniqueId]?.id === blank.word.id
    );

  const handleCompleteClick = () => {
    navigate(`/story/${storyId}/complete`);
  };

  const renderParagraph = () => {
    return parsedParagraphs[currentParagraphIndex].map((part, index) => {
      if (!part.blank) return <span key={`text-${index}`}>{part.text}</span>;
      const { blank, uniqueId } = part;
      return (
        <DroppableBlank
          key={uniqueId}
          uniqueId={uniqueId}
          blank={blank}
          filledWord={filledBlanks[uniqueId]}
          isWrong={wrongAttempt === uniqueId}
        />
      );
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
        {paragraph.audio ? (
          <button
            type="button"
            className="nes-btn is-primary"
            onClick={() => onPlayAudio(paragraph.audio)}
          >
            reading
          </button>
        ) : (
          <div></div>
        )}

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
        <p>{renderParagraph()}</p>
      </div>

      {hasUnavailableWords && (
        <p role="status" style={{ fontSize: '0.75rem', marginTop: '0.75rem' }}>
          Some words are unavailable. You can still read the story.
        </p>
      )}

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
          style={{
            visibility:
              paragraphNumber < totalParagraphs ? 'visible' : 'hidden',
          }}
        >
          Next &gt;
        </button>
      </div>
    </div>
  );
}

export default StoryContent;
