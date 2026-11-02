import { StrictMode } from 'react';
import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getStoryById } from '../api/storyApi';
import { useStory } from './useStory';

vi.mock('../api/storyApi', () => ({ getStoryById: vi.fn() }));

function deferredRequest() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

beforeEach(() => {
  vi.mocked(getStoryById).mockReset();
});

describe('useStory request ownership', () => {
  it('never returns the loaded story on the first render of another route', async () => {
    const nextRequest = deferredRequest();
    vi.mocked(getStoryById)
      .mockResolvedValueOnce({ id: 'A' })
      .mockReturnValueOnce(nextRequest.promise);
    const renders = [];
    const { rerender } = renderHook(
      ({ id }) => {
        const state = useStory(id);
        renders.push({ id, ...state });
        return state;
      },
      { initialProps: { id: 'A' } }
    );
    await act(async () => {});
    renders.length = 0;

    rerender({ id: 'B' });

    expect(renders[0]).toMatchObject({
      id: 'B',
      story: null,
      loading: true,
      error: null,
    });
    expect(renders.every((state) => state.story === null)).toBe(true);
    await act(async () => nextRequest.resolve({ id: 'B' }));
  });

  it('does not carry the old error into the first render of another route', async () => {
    const nextRequest = deferredRequest();
    vi.mocked(getStoryById)
      .mockRejectedValueOnce(new Error('Story A failed'))
      .mockReturnValueOnce(nextRequest.promise);
    const renders = [];
    const { rerender } = renderHook(
      ({ id }) => {
        const state = useStory(id);
        renders.push(state);
        return state;
      },
      { initialProps: { id: 'A' } }
    );
    await act(async () => {});
    renders.length = 0;

    rerender({ id: 'B' });

    expect(renders[0]).toMatchObject({
      story: null,
      loading: true,
      error: null,
    });
    await act(async () => nextRequest.resolve({ id: 'B' }));
  });

  it('keeps the new story when an older request finishes later', async () => {
    const oldRequest = deferredRequest();
    const newRequest = deferredRequest();
    vi.mocked(getStoryById)
      .mockReturnValueOnce(oldRequest.promise)
      .mockReturnValueOnce(newRequest.promise);
    const { result, rerender } = renderHook(({ id }) => useStory(id), {
      initialProps: { id: 'A' },
    });

    rerender({ id: 'B' });
    await act(async () => newRequest.resolve({ id: 'B' }));
    await act(async () => oldRequest.resolve({ id: 'A' }));

    expect(result.current.story).toEqual({ id: 'B' });
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(getStoryById.mock.calls[0][1].signal.aborted).toBe(true);
  });

  it('ignores an old rejection and finally while the next request is pending', async () => {
    const oldRequest = deferredRequest();
    const newRequest = deferredRequest();
    vi.mocked(getStoryById)
      .mockReturnValueOnce(oldRequest.promise)
      .mockReturnValueOnce(newRequest.promise);
    const { result, rerender } = renderHook(({ id }) => useStory(id), {
      initialProps: { id: 'A' },
    });

    rerender({ id: 'B' });
    await act(async () => oldRequest.reject(new Error('Old request failed')));

    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(true);
    await act(async () => newRequest.resolve({ id: 'B' }));
    expect(result.current.story).toEqual({ id: 'B' });
  });

  it('lets only the latest refetch update the story or finish loading', async () => {
    const firstRefresh = deferredRequest();
    const secondRefresh = deferredRequest();
    vi.mocked(getStoryById)
      .mockResolvedValueOnce({ id: 'A', title: 'Initial' })
      .mockReturnValueOnce(firstRefresh.promise)
      .mockReturnValueOnce(secondRefresh.promise);
    const { result } = renderHook(() => useStory('A'));
    await act(async () => {});

    act(() => {
      void result.current.refetch();
      void result.current.refetch();
    });
    await act(async () => firstRefresh.resolve({ id: 'A', title: 'Old' }));

    expect(result.current.loading).toBe(true);
    expect(getStoryById.mock.calls[1][1].signal.aborted).toBe(true);
    await act(async () => secondRefresh.resolve({ id: 'A', title: 'New' }));
    expect(result.current.story).toEqual({ id: 'A', title: 'New' });
    expect(result.current.loading).toBe(false);
  });

  it('reports a current failure and clears it when a retry succeeds', async () => {
    vi.mocked(getStoryById)
      .mockRejectedValueOnce(new Error('Service unavailable'))
      .mockResolvedValueOnce({ id: 'A' });
    const { result } = renderHook(() => useStory('A'));
    await act(async () => {});
    expect(result.current.error).toBe('Service unavailable');
    expect(result.current.loading).toBe(false);

    await act(async () => result.current.refetch());
    expect(result.current.story).toEqual({ id: 'A' });
    expect(result.current.error).toBeNull();
  });

  it('does not display cancellation as a failure', async () => {
    vi.mocked(getStoryById).mockRejectedValueOnce(
      new DOMException('The request was aborted.', 'AbortError')
    );
    const { result } = renderHook(() => useStory('A'));
    await act(async () => {});

    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('cancels on unmount and ignores a saved retry callback afterwards', async () => {
    const request = deferredRequest();
    vi.mocked(getStoryById).mockReturnValue(request.promise);
    const { result, unmount } = renderHook(() => useStory('A'));
    const retryAfterUnmount = result.current.refetch;
    const requestOptions = getStoryById.mock.calls[0][1];

    unmount();
    const retryResult = retryAfterUnmount();
    await act(async () => {
      request.resolve({ id: 'A' });
      await retryResult;
    });

    expect(getStoryById).toHaveBeenCalledTimes(1);
    expect(requestOptions.signal.aborted).toBe(true);
  });

  it('handles StrictMode cleanup even if the canceled request still resolves', async () => {
    const discardedRequest = deferredRequest();
    const activeRequest = deferredRequest();
    vi.mocked(getStoryById)
      .mockReturnValueOnce(discardedRequest.promise)
      .mockReturnValueOnce(activeRequest.promise);
    const { result } = renderHook(() => useStory('A'), {
      wrapper: StrictMode,
    });

    await act(async () => activeRequest.resolve({ id: 'A', title: 'Current' }));
    await act(async () => discardedRequest.resolve({ id: 'A', title: 'Old' }));

    expect(result.current.story).toEqual({ id: 'A', title: 'Current' });
    expect(getStoryById.mock.calls[0][1].signal.aborted).toBe(true);
    expect(getStoryById.mock.calls[1][1].signal.aborted).toBe(false);
  });

  it('does not let a retry callback from the previous route start another request', async () => {
    vi.mocked(getStoryById).mockResolvedValue({ id: 'A' });
    const { result, rerender } = renderHook(({ id }) => useStory(id), {
      initialProps: { id: 'A' },
    });
    await act(async () => {});
    const retryPreviousStory = result.current.refetch;

    rerender({ id: 'B' });
    await act(async () => retryPreviousStory());

    expect(getStoryById).toHaveBeenCalledTimes(2);
    expect(getStoryById.mock.calls[1][0]).toBe('B');
  });

  it('clears the previous story when there is no story ID', async () => {
    vi.mocked(getStoryById).mockResolvedValue({ id: 'A' });
    const { result, rerender } = renderHook(({ id }) => useStory(id), {
      initialProps: { id: 'A' },
    });
    await act(async () => {});

    rerender({ id: null });

    expect(result.current.story).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(getStoryById).toHaveBeenCalledTimes(1);
  });
});
