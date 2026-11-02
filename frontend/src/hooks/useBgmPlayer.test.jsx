import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useBgmPlayer } from './useBgmPlayer';
import { deferred, mockAudio } from '../testUtils/audio';

const config = {
  ok: true,
  json: async () => ({ menu_bgm: { audio_url: '/menu.mp3' } }),
};

beforeEach(() => {
  vi.mocked(fetch).mockResolvedValue(config);
  vi.spyOn(console, 'warn').mockImplementation(() => {});
});

afterEach(() => vi.useRealTimers());

describe('menu background music lifecycle', () => {
  it('aborts configuration loading and ignores its late response after unmount', async () => {
    const pending = deferred();
    vi.mocked(fetch).mockReturnValue(pending.promise);
    const audio = mockAudio();
    const view = renderHook(() => useBgmPlayer());
    const signal = vi.mocked(fetch).mock.calls.at(-1)[1]?.signal;
    view.unmount();
    await act(async () => pending.resolve(config));
    expect(signal?.aborted).toBe(true);
    expect(audio).toHaveLength(0);
  });

  it('clears the autoplay hint timer on unmount', async () => {
    vi.useFakeTimers();
    const audio = mockAudio(() =>
      Promise.reject(new DOMException('Blocked', 'NotAllowedError'))
    );
    const view = renderHook(() => useBgmPlayer());
    await act(async () => {});
    expect(view.result.current.isMusicPlaying).toBe(false);
    expect(view.result.current.showHint).toBe(true);
    expect(vi.getTimerCount()).toBe(1);
    view.unmount();
    expect(audio[0].pause).toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('ignores a late autoplay rejection after unmount', async () => {
    const pending = deferred();
    const audio = mockAudio(() => pending.promise);
    const view = renderHook(() => useBgmPlayer());
    await waitFor(() => expect(audio).toHaveLength(1));
    vi.useFakeTimers();
    view.unmount();
    await act(async () => pending.reject(new Error('Late failure')));
    expect(vi.getTimerCount()).toBe(0);
  });

  it('does not mark music as playing when a cancelled play resolves', async () => {
    const pending = deferred();
    const audio = mockAudio(() => pending.promise);
    const view = renderHook(() => useBgmPlayer());
    await waitFor(() => expect(audio).toHaveLength(1));
    act(() => view.result.current.toggleMusic());
    await act(async () => pending.resolve());
    expect(view.result.current.isMusicPlaying).toBe(false);
    expect(audio[0].pause).toHaveBeenCalled();
  });

  it('keeps a newer successful play when an earlier request rejects', async () => {
    const pending = deferred();
    const audio = mockAudio(() => pending.promise);
    const view = renderHook(() => useBgmPlayer());
    await waitFor(() => expect(audio).toHaveLength(1));
    act(() => view.result.current.toggleMusic());
    audio[0].play.mockResolvedValue(undefined);
    await act(async () => view.result.current.toggleMusic());
    await act(async () => pending.reject(new Error('Old request failed')));
    expect(view.result.current.isMusicPlaying).toBe(true);
    expect(view.result.current.showHint).toBe(false);
  });
});
