import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { getAllStories } from '../api/storyApi';
import { useStories } from './useStories';

vi.mock('../api/storyApi', () => ({ getAllStories: vi.fn() }));

beforeEach(() => {
  vi.mocked(getAllStories).mockReset();
});

it.each([null, 'private transport detail', { message: 42 }])(
  'shows a safe fallback for an unexpected rejection: %j',
  async (rejection) => {
    vi.mocked(getAllStories).mockRejectedValue(rejection);
    const { result } = renderHook(() => useStories());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Unable to load stories.');
    expect(result.current.stories).toEqual([]);
  }
);

it('preserves a useful error message without requiring an Error instance', async () => {
  vi.mocked(getAllStories).mockRejectedValue({ message: 'Please try again.' });
  const { result } = renderHook(() => useStories());

  await waitFor(() => expect(result.current.loading).toBe(false));

  expect(result.current.error).toBe('Please try again.');
});
