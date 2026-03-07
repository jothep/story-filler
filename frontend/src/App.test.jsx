import { render, screen, cleanup, waitFor } from '@testing-library/react'; 
import { describe, it, expect, vi, afterEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { DndContext } from '@dnd-kit/core';
import StoryPlayer from './pages/StoryPlayer';

const MOCK_SUCCESS_DATA = {
  paragraphs: [
    {
      id: 1,
      text: 'On a bright moonlit night',
      audio: 'audio.m4a',
      blank_links: [],
    },
  ],
  words_in_bank: [
    {
      id: 1,
      maori_word: 'kātao',
      english_translation: 'water',
    },
  ],
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const renderComponent = (mock) => {
  vi.mocked(fetch).mockResolvedValue(mock);

  if (!mock.ok) {
    vi.spyOn(console, 'error').mockImplementation(() => {});
  }

  render(
    <MemoryRouter initialEntries={['/story/1']}>
      <DndContext>
        <Routes>
          <Route path="/story/:storyId" element={<StoryPlayer />} />
        </Routes>
      </DndContext>
    </MemoryRouter>
  );
};

describe('StoryPlayer Component', () => {
  it('should load and display story content on success', async () => {
    renderComponent({
      ok: true,
      json: async () => MOCK_SUCCESS_DATA,
    });

    await waitFor(() => {
      expect(screen.queryByText(/^Loading story...$/i)).not.toBeInTheDocument();
    });

    const wordButton = await screen.findByText('kātao');
    expect(wordButton).toBeInTheDocument();
    expect(
      await screen.findByText(/On a bright moonlit night/i)
    ).toBeInTheDocument();
  });

  it('should display an error message if fetch fails', async () => {
    renderComponent({ ok: false });

    await waitFor(() => {
      expect(screen.queryByText(/^Loading story...$/i)).not.toBeInTheDocument();
    });

    // Check for the new error UI components
    const errorHeading = await screen.findByText(/Oops!/i);
    expect(errorHeading).toBeInTheDocument();

    const retryButton = await screen.findByText(/Try Again/i);
    expect(retryButton).toBeInTheDocument();
  });
});