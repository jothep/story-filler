import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DndContext } from '@dnd-kit/core';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import StoryContent from './StoryContent';
import {
  useWordInteraction,
  WordInteractionProvider,
} from '../context/WordInteractionContext';

const playback = vi.hoisted(() => ({}));
vi.mock('../context/StoryPlaybackContext', () => ({
  useStoryPlayback: () => playback,
}));

const correctWord = { id: 1, maori_word: 'aroha' };
const wrongWord = { id: 2, maori_word: 'kai' };

// These controls submit dnd-kit events through the real interaction provider.
// Pointer geometry belongs to browser testing; answer evaluation is not mocked.
function DropControls() {
  const { handleDragEnd, wrongAttempt } = useWordInteraction();
  const drop = (
    wordId,
    target = 'blank-10-1',
    expectedWordId = correctWord.id
  ) => {
    handleDragEnd({
      active: { id: wordId },
      over: {
        id: target,
        data: { current: { type: 'blank', correctWordId: expectedWordId } },
      },
    });
  };
  return (
    <>
      <button onClick={() => drop(wrongWord.id)}>Drop wrong answer</button>
      <button onClick={() => drop(correctWord.id)}>Drop correct answer</button>
      <button onClick={() => drop(correctWord.id, 'unrelated-blank')}>
        Drop elsewhere
      </button>
      <button onClick={() => drop(wrongWord.id, 'blank-11-1', wrongWord.id)}>
        Fill the next paragraph
      </button>
      <output aria-label="Wrong attempt">{wrongAttempt}</output>
    </>
  );
}

function renderStory(paragraphs) {
  Object.assign(playback, {
    story: { paragraphs },
    currentParagraph: paragraphs[0],
    currentParagraphIndex: 0,
  });
  return render(
    <MemoryRouter initialEntries={['/story/7']}>
      <Routes>
        <Route
          path="/story/:storyId"
          element={
            <WordInteractionProvider wordsInBank={[correctWord, wrongWord]}>
              <DndContext>
                <StoryContent />
                <DropControls />
              </DndContext>
            </WordInteractionProvider>
          }
        />
        <Route
          path="/story/:storyId/complete"
          element={<p>Story completed</p>}
        />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  Object.assign(playback, {
    handleNextParagraph: vi.fn(),
    handlePrevParagraph: vi.fn(),
    handlePlayParagraphAudio: vi.fn(),
  });
});

describe('StoryContent', () => {
  it.each([
    [
      'a null linked word',
      [{ id: 10, placeholder: '__BLANK_1__', word: null }],
    ],
    ['a missing link', []],
    ['missing links', undefined],
  ])('renders %s without crashing or completing the story', (_, blankLinks) => {
    renderStory([
      { id: 5, text: 'A __BLANK_1__ story.', blank_links: blankLinks },
      { id: 6, text: 'The next paragraph.' },
    ]);

    expect(screen.getByLabelText('Word unavailable')).toBeInTheDocument();
    expect(screen.getByText('A')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Drop correct answer'));
    expect(screen.queryByText('Complete Story!')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Next >' }));
    expect(playback.handleNextParagraph).toHaveBeenCalledOnce();
  });

  it('requires the correct answer and still opens the completion page', () => {
    renderStory([
      {
        id: 5,
        text: 'A __BLANK_1__ story.',
        blank_links: [
          { id: 10, placeholder: '__BLANK_1__', word: correctWord },
        ],
      },
    ]);

    fireEvent.click(screen.getByText('Drop wrong answer'));
    expect(screen.getByLabelText('Wrong attempt')).toHaveTextContent(
      'blank-10-1'
    );
    expect(screen.queryByText('Complete Story!')).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Drop correct answer'));
    expect(screen.getByLabelText('Wrong attempt')).toBeEmptyDOMElement();
    expect(screen.getByText('aroha')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Complete Story!'));
    expect(screen.getByText('Story completed')).toBeInTheDocument();
  });

  it('does not use a filled blank from another paragraph to complete this story', () => {
    renderStory([
      {
        id: 5,
        text: 'A __BLANK_1__ story.',
        blank_links: [
          { id: 10, placeholder: '__BLANK_1__', word: correctWord },
        ],
      },
    ]);
    fireEvent.click(screen.getByText('Drop elsewhere'));
    expect(screen.queryByText('Complete Story!')).not.toBeInTheDocument();
  });

  it('waits for blanks in later paragraphs before offering completion', () => {
    renderStory([
      {
        id: 5,
        text: 'A __BLANK_1__ story.',
        blank_links: [
          { id: 10, placeholder: '__BLANK_1__', word: correctWord },
        ],
      },
      {
        id: 6,
        text: 'Another __BLANK_2__.',
        blank_links: [{ id: 11, placeholder: '__BLANK_2__', word: wrongWord }],
      },
    ]);
    fireEvent.click(screen.getByText('Drop correct answer'));
    expect(screen.getByText('aroha')).toBeInTheDocument();
    expect(screen.queryByText('Complete Story!')).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Fill the next paragraph'));
    expect(screen.getByText('Complete Story!')).toBeInTheDocument();
  });

  it('keeps stories without blanks readable without a completion button', () => {
    renderStory([{ id: 5, text: 'Read this story.' }]);
    expect(screen.getByText('Read this story.')).toBeInTheDocument();
    expect(screen.queryByText('Complete Story!')).not.toBeInTheDocument();
  });
});
