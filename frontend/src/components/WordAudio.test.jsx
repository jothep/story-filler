import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import WordAudio from './WordAudio';
import { useWordInteraction } from '../context/WordInteractionContext';
import { deferred, mockAudio } from '../testUtils/audio';

vi.mock('../context/WordInteractionContext', () => ({
  useWordInteraction: vi.fn(),
}));

const word = {
  id: 1,
  maori_word: 'wai',
  english_translation: 'water',
  maori_audio: '/wai.mp3',
  english_audio: '/water.mp3',
};

beforeEach(() => {
  useWordInteraction.mockReturnValue({ selectedWord: word });
});

describe('word audio ownership', () => {
  it('replaces previous word audio instead of overlapping it', async () => {
    const audio = mockAudio();
    render(<WordAudio />);
    fireEvent.click(screen.getAllByRole('button')[0]);
    fireEvent.click(screen.getAllByRole('button')[1]);
    await act(async () => {});
    expect(audio).toHaveLength(2);
    expect(audio[0].pause).toHaveBeenCalled();
    expect(audio[1].src).toBe('/water.mp3');
  });

  it('stops audio when the word changes and when the component unmounts', async () => {
    const audio = mockAudio();
    const view = render(<WordAudio />);
    fireEvent.click(screen.getAllByRole('button')[0]);
    useWordInteraction.mockReturnValue({ selectedWord: { ...word, id: 2 } });
    view.rerender(<WordAudio />);
    expect(audio[0].pause).toHaveBeenCalled();
    fireEvent.click(screen.getAllByRole('button')[0]);
    view.unmount();
    await act(async () => {});
    expect(audio[1].pause).toHaveBeenCalled();
  });

  it('handles a rejected play and clears the message on manual retry', async () => {
    const play = vi
      .fn()
      .mockRejectedValueOnce(new Error('Playback blocked'))
      .mockResolvedValue(undefined);
    const audio = mockAudio(play);
    render(<WordAudio />);
    await act(async () => fireEvent.click(screen.getAllByRole('button')[0]));
    expect(screen.getByRole('status')).toHaveTextContent(/unable to play/i);
    await act(async () => fireEvent.click(screen.getAllByRole('button')[0]));
    expect(audio).toHaveLength(2);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('ignores a rejected play after another word has been selected', async () => {
    const pending = deferred();
    mockAudio(() => pending.promise);
    const view = render(<WordAudio />);
    fireEvent.click(screen.getAllByRole('button')[0]);
    useWordInteraction.mockReturnValue({ selectedWord: { ...word, id: 2 } });
    view.rerender(<WordAudio />);
    await act(async () => pending.reject(new Error('Previous word failed')));
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('does not display a media error from a replaced recording', async () => {
    const audio = mockAudio();
    render(<WordAudio />);
    fireEvent.click(screen.getAllByRole('button')[0]);
    fireEvent.click(screen.getAllByRole('button')[1]);
    await act(async () => audio[0].emit('error'));
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(audio[1].pause).not.toHaveBeenCalled();
  });

  it('disables unavailable recordings', () => {
    mockAudio();
    useWordInteraction.mockReturnValue({
      selectedWord: { ...word, maori_audio: null, english_audio: null },
    });
    render(<WordAudio />);
    for (const button of screen.getAllByRole('button'))
      expect(button).toBeDisabled();
  });
});
