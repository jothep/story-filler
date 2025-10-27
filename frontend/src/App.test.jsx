import { render, screen, cleanup, waitFor } from '@testing-library/react'; // 1. 导入 waitFor
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
    // 压制我们预期的控制台错误
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

    // 2. (修复) 使用 await waitFor 来等待 "Loading..." 消失
    await waitFor(() => {
      expect(screen.queryByText(/^Loading story...$/i)).not.toBeInTheDocument();
    });

    // (保持不变) 现在的检查是安全的，因为加载已完成
    const wordButton = await screen.findByText('kātao');
    expect(wordButton).toBeInTheDocument();
    expect(
      await screen.findByText(/On a bright moonlit night/i)
    ).toBeInTheDocument();
  });

  it('should display an error message if fetch fails', async () => {
    renderComponent({ ok: false });

    // 3. (修复) 同样，等待 "Loading..." 消失
    await waitFor(() => {
      expect(screen.queryByText(/^Loading story...$/i)).not.toBeInTheDocument();
    });

    // (保持不变) 现在检查错误信息是安全的
    const errorMessage = await screen.findByText(/Error loading story:/i);
    expect(errorMessage).toBeInTheDocument();
  });
});