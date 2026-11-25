import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import WordPic from './WordPic';
import { useWordInteraction } from '../context/WordInteractionContext';

vi.mock('../context/WordInteractionContext', () => ({
  useWordInteraction: vi.fn(),
}));

const word = { id: 1, key: 'moon', text: 'marama', translation: 'moon' };

beforeEach(() => {
  useWordInteraction.mockReturnValue({ selectedWord: null });
});

describe('WordPic', () => {
  it('shows the picture with the translation as its description', () => {
    useWordInteraction.mockReturnValue({
      selectedWord: { ...word, image: '/moon.jpg' },
    });
    render(<WordPic />);
    expect(screen.getByRole('img', { name: 'moon' })).toHaveAttribute(
      'src',
      '/moon.jpg'
    );
  });

  it('shows a placeholder for a word without a picture', () => {
    useWordInteraction.mockReturnValue({
      selectedWord: { ...word, image: null },
    });
    render(<WordPic />);
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.getByText('No picture yet')).toBeInTheDocument();
  });

  it('shows the placeholder when the picture fails to load', () => {
    useWordInteraction.mockReturnValue({
      selectedWord: { ...word, image: '/missing.jpg' },
    });
    render(<WordPic />);
    fireEvent.error(screen.getByRole('img'));
    expect(screen.getByText('No picture yet')).toBeInTheDocument();
  });
});
