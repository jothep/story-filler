import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import StoryPlayerUI from './StoryPlayerUI';

const handlers = vi.hoisted(() => ({
  handleDragStart: vi.fn(),
  handleDragEnd: vi.fn(),
}));
const dragContext = vi.hoisted(() => ({ props: null }));

vi.mock('@dnd-kit/core', () => ({
  DndContext: (props) => {
    dragContext.props = props;
    return props.children;
  },
  DragOverlay: ({ children }) => (
    <div data-testid="drag-overlay">{children}</div>
  ),
  useSensor: vi.fn(),
  useSensors: vi.fn(),
  MouseSensor: vi.fn(),
  TouchSensor: vi.fn(),
}));
vi.mock('../context/WordInteractionContext', () => ({
  useWordInteraction: () => handlers,
}));
vi.mock('../context/StoryPlaybackContext', () => ({
  useStoryPlayback: () => ({
    story: {
      title: 'Story',
      paragraphs: [],
      words_in_bank: [{ id: 1, maori_word: 'aroha' }],
    },
  }),
}));
vi.mock('../components/StoryPicture', () => ({ default: () => null }));
vi.mock('../components/WordList', () => ({ default: () => null }));
vi.mock('../components/WordPic', () => ({ default: () => null }));
vi.mock('../components/WordAudio', () => ({ default: () => null }));
vi.mock('../components/TriggerTips', () => ({ default: () => null }));

function renderAndStartDrag() {
  const view = render(
    <MemoryRouter>
      <StoryPlayerUI />
    </MemoryRouter>
  );
  act(() => dragContext.props.onDragStart({ active: { id: 1 } }));
  expect(document.body).toHaveClass('dragging');
  expect(screen.getByTestId('drag-overlay')).toHaveTextContent('aroha');
  return view;
}

beforeEach(() => {
  handlers.handleDragStart.mockReset();
  handlers.handleDragEnd.mockReset();
  document.body.classList.remove('dragging');
});

describe('StoryPlayerUI drag lifecycle', () => {
  it('clears the overlay and body state when a drag is cancelled', () => {
    renderAndStartDrag();
    act(() => dragContext.props.onDragCancel());
    expect(document.body).not.toHaveClass('dragging');
    expect(screen.queryByTestId('drag-overlay')).not.toBeInTheDocument();
    expect(handlers.handleDragEnd).not.toHaveBeenCalled();
  });

  it('clears body state when leaving during a drag', () => {
    const { unmount } = renderAndStartDrag();
    unmount();
    expect(document.body).not.toHaveClass('dragging');
    expect(handlers.handleDragEnd).not.toHaveBeenCalled();
  });

  it('still forwards a completed drop and clears visual state', () => {
    renderAndStartDrag();
    const event = { active: { id: 1 }, over: { id: 'blank-10-1' } };
    act(() => dragContext.props.onDragEnd(event));
    expect(handlers.handleDragEnd).toHaveBeenCalledExactlyOnceWith(event);
    expect(document.body).not.toHaveClass('dragging');
    expect(screen.queryByTestId('drag-overlay')).not.toBeInTheDocument();
  });
});
