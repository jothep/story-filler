import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getAllStories, getStoryById } from './storyApi';

vi.mock('../config/api', () => ({
  getApiUrl: (path) => `https://api.example.test${path}`,
}));

function response(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

beforeEach(() => {
  vi.mocked(fetch).mockReset();
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

describe('story API contracts', () => {
  it('returns the bare story list when called without options', async () => {
    const stories = [{ id: 1, title: 'A story' }];
    vi.mocked(fetch).mockResolvedValue(response(stories));

    await expect(getAllStories()).resolves.toEqual(stories);
    expect(fetch.mock.calls[0][0]).toBe(
      'https://api.example.test/api/stories/'
    );
  });

  it('returns the story object and forwards the exact cancellation signal', async () => {
    const story = { id: 1, paragraphs: [], words_in_bank: [] };
    const controller = new AbortController();
    vi.mocked(fetch).mockResolvedValue(response(story));

    await expect(
      getStoryById(1, { signal: controller.signal })
    ).resolves.toEqual(story);
    expect(fetch).toHaveBeenCalledWith(
      'https://api.example.test/api/stories/1/',
      { signal: controller.signal }
    );
  });

  it('also accepts a cancellation signal for the story list', async () => {
    const controller = new AbortController();
    vi.mocked(fetch).mockResolvedValue(response([]));

    await getAllStories({ signal: controller.signal });

    expect(fetch.mock.calls[0][1].signal).toBe(controller.signal);
  });

  it('keeps the existing detail-not-found message', async () => {
    vi.mocked(fetch).mockResolvedValue(response({ error: 'Not found' }, 404));

    await expect(getStoryById('missing')).rejects.toThrow(
      'Story not found. It may have been removed or the link is incorrect.'
    );
  });

  it.each([
    [{ error: 'Service unavailable' }, 'Service unavailable'],
    [
      { error: 'Service unavailable', detail: 'Please try again later.' },
      'Please try again later.',
    ],
  ])('preserves safe structured server errors', async (body, message) => {
    vi.mocked(fetch).mockResolvedValue(response(body, 500));

    await expect(getAllStories()).rejects.toThrow(message);
    expect(console.error).toHaveBeenCalledTimes(1);
  });

  it('handles a non-JSON error without exposing its response body', async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response('<html>Internal proxy error</html>', {
        status: 502,
        statusText: 'Bad Gateway',
      })
    );

    await expect(getStoryById(1)).rejects.toThrow(
      'Server error (502: Bad Gateway)'
    );
  });

  it.each([getAllStories, () => getStoryById(1)])(
    'preserves the friendly network-error message',
    async (request) => {
      vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'));

      await expect(request()).rejects.toThrow(
        'Unable to connect to the server. Please check your internet connection.'
      );
    }
  );

  it.each([getAllStories, () => getStoryById(1)])(
    'propagates cancellation without logging an application failure',
    async (request) => {
      const aborted = new DOMException('Canceled', 'AbortError');
      vi.mocked(fetch).mockRejectedValue(aborted);

      await expect(request()).rejects.toBe(aborted);
      expect(console.error).not.toHaveBeenCalled();
    }
  );

  it('does not turn cancellation during error-body parsing into a server error', async () => {
    const aborted = new DOMException('Canceled', 'AbortError');
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
      json: vi.fn().mockRejectedValue(aborted),
    });

    await expect(getStoryById(1)).rejects.toBe(aborted);
    expect(console.error).not.toHaveBeenCalled();
  });
});
