import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  StoryPlaybackProvider,
  useStoryPlayback,
} from './StoryPlaybackContext';
import { deferred, mockAudio } from '../testUtils/audio';

const story = {
  id: 1,
  paragraphs: [
    { id: 1, audio: '/first.mp3' },
    { id: 2, audio: '/second.mp3' },
  ],
};

function Controls() {
  const playback = useStoryPlayback();
  return (
    <>
      <span>Paragraph {playback.currentParagraphIndex + 1}</span>
      <span>Music {playback.isMusicPlaying ? 'playing' : 'stopped'}</span>
      <button
        onClick={() =>
          playback.handlePlayParagraphAudio(playback.currentParagraph.audio)
        }
      >
        Read
      </button>
      <button onClick={playback.handleNextParagraph}>Next</button>
      <button onClick={playback.handlePrevParagraph}>Previous</button>
      <button onClick={playback.handleToggleMusic}>Toggle music</button>
    </>
  );
}

function player(value = story) {
  return (
    <StoryPlaybackProvider story={value}>
      <Controls />
    </StoryPlaybackProvider>
  );
}

beforeEach(() => {
  vi.spyOn(window, 'alert').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

describe('story audio ownership', () => {
  it('stops narration on unmount and ignores late media errors', async () => {
    const audio = mockAudio();
    const view = render(player());
    fireEvent.click(screen.getByText('Read'));
    view.unmount();
    await act(async () => audio[0].emit('error'));
    expect(audio[0].pause).toHaveBeenCalled();
    expect(window.alert).not.toHaveBeenCalled();
  });

  it('does not restart a cancelled paragraph after a late play rejection', async () => {
    const pending = deferred();
    const audio = mockAudio(() => pending.promise);
    render(player());
    fireEvent.click(screen.getByText('Read'));
    fireEvent.click(screen.getByText('Next'));
    await act(async () =>
      pending.reject(new DOMException('Interrupted', 'AbortError'))
    );
    await act(async () => audio[0].emit('canplaythrough'));
    expect(audio[0].pause).toHaveBeenCalled();
    expect(audio[0].play).toHaveBeenCalledTimes(1);
    expect(audio[0].load).not.toHaveBeenCalled();
    expect(window.alert).not.toHaveBeenCalled();
  });

  it('replaces narration and ignores errors from the replaced element', async () => {
    const audio = mockAudio();
    render(player());
    fireEvent.click(screen.getByText('Read'));
    fireEvent.click(screen.getByText('Read'));
    await act(async () => audio[0].emit('error'));
    expect(audio).toHaveLength(2);
    expect(audio[0].pause).toHaveBeenCalled();
    expect(audio[1].pause).not.toHaveBeenCalled();
    expect(window.alert).not.toHaveBeenCalled();
  });

  it('reports a current playback failure once and lets the user retry', async () => {
    const pending = deferred();
    const play = vi
      .fn()
      .mockReturnValueOnce(pending.promise)
      .mockResolvedValue(undefined);
    const audio = mockAudio(play);
    render(player());
    fireEvent.click(screen.getByText('Read'));
    await act(async () => {
      audio[0].emit('error');
      pending.reject(new Error('Media failed'));
    });
    expect(window.alert).toHaveBeenCalledTimes(1);
    await act(async () => fireEvent.click(screen.getByText('Read')));
    expect(audio).toHaveLength(2);
    expect(window.alert).toHaveBeenCalledTimes(1);
  });

  it('resets narration and paragraph selection when the story changes', async () => {
    const audio = mockAudio();
    const view = render(player());
    fireEvent.click(screen.getByText('Next'));
    fireEvent.click(screen.getByText('Read'));
    view.rerender(
      player({ id: 2, paragraphs: [{ id: 3, audio: '/new.mp3' }] })
    );
    expect(screen.getByText('Paragraph 1')).toBeInTheDocument();
    expect(audio[0].pause).toHaveBeenCalled();
  });

  it('reflects blocked background music and supports a successful manual retry', async () => {
    const audio = mockAudio(() =>
      Promise.reject(new DOMException('Blocked', 'NotAllowedError'))
    );
    render(player({ ...story, background_music_url: '/bgm.mp3' }));
    await act(async () => {});
    expect(screen.getByText('Music stopped')).toBeInTheDocument();
    audio[0].play.mockResolvedValue(undefined);
    await act(async () => fireEvent.click(screen.getByText('Toggle music')));
    expect(screen.getByText('Music playing')).toBeInTheDocument();
  });

  it('keeps background music stopped when an earlier play finishes after toggle-off', async () => {
    const pending = deferred();
    const audio = mockAudio(() => pending.promise);
    render(player({ ...story, background_music_url: '/bgm.mp3' }));
    fireEvent.click(screen.getByText('Toggle music'));
    await act(async () => pending.resolve());
    expect(audio[0].pause).toHaveBeenCalled();
    expect(screen.getByText('Music stopped')).toBeInTheDocument();
  });

  it("ignores a previous story's delayed music failure", async () => {
    const pending = deferred();
    const play = vi
      .fn()
      .mockReturnValueOnce(pending.promise)
      .mockResolvedValue(undefined);
    const audio = mockAudio(play);
    const view = render(player({ ...story, background_music_url: '/old.mp3' }));
    await act(async () =>
      view.rerender(
        player({ ...story, id: 2, background_music_url: '/new.mp3' })
      )
    );
    await act(async () =>
      pending.reject(new Error('Old background music failed'))
    );
    expect(audio[0].pause).toHaveBeenCalled();
    expect(audio[1].pause).not.toHaveBeenCalled();
    expect(screen.getByText('Music playing')).toBeInTheDocument();
  });
});
