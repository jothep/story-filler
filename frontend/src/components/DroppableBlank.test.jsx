import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import DroppableBlank from './DroppableBlank';

const dragState = vi.hoisted(() => ({ active: null, isOver: false }));
const useDroppable = vi.hoisted(() => vi.fn());

vi.mock('@dnd-kit/core', () => ({
  useDroppable,
  useDndContext: () => ({ active: dragState.active }),
}));

beforeEach(() => {
  dragState.active = null;
  dragState.isOver = false;
  useDroppable.mockImplementation(() => ({
    isOver: dragState.isOver,
    setNodeRef: vi.fn(),
  }));
});

describe('DroppableBlank', () => {
  it('keeps a missing word readable and disables its drop target', () => {
    dragState.active = { id: 1 };
    dragState.isOver = true;
    render(
      <DroppableBlank
        blank={{ word: null }}
        uniqueId="missing"
        filledWord={{ id: 1, maori_word: 'stale answer' }}
        isWrong={true}
      />
    );

    expect(useDroppable).toHaveBeenLastCalledWith(
      expect.objectContaining({ id: 'missing', disabled: true })
    );
    const blank = screen.getByLabelText('Word unavailable');
    expect(blank).toHaveTextContent('Unavailable');
    expect(blank).toHaveStyle({ animation: 'none', transform: 'scale(1)' });
    expect(screen.queryByText('stale answer')).not.toBeInTheDocument();
  });

  it('accepts drops only until an available blank is filled', () => {
    const props = {
      blank: { word: { id: 4 } },
      uniqueId: 'blank-4',
      isWrong: false,
    };
    const { rerender } = render(<DroppableBlank {...props} />);
    expect(useDroppable).toHaveBeenLastCalledWith({
      id: 'blank-4',
      data: { type: 'blank', correctWordId: 4 },
      disabled: false,
    });

    rerender(
      <DroppableBlank {...props} filledWord={{ id: 4, maori_word: 'aroha' }} />
    );
    expect(screen.getByText('aroha')).toBeInTheDocument();
    expect(useDroppable).toHaveBeenLastCalledWith(
      expect.objectContaining({ disabled: true })
    );
  });
});
