// src/App.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// (MOCK_STORY_DATA 保持不变)
const MOCK_STORY_DATA = {
  id: 3,
  title: 'Kupe and the Octopus', 
  paragraphs: [
    {
      id: 1,
      order: 1,
      text: 'This is the first paragraph with a __BLANK_test__.',
      audio: '/media/audio/1.m4a',
      blank_links: [
        {
          id: 1,
          placeholder: '__BLANK_test__',
          word: { id: 1, maori_word: 'test' }
        }
      ]
    }
  ],
  words_in_bank: [
    { 
      id: 1, 
      maori_word: 'test', 
      english_translation: 'Test' 
    }
  ]
};

describe('App Component', () => {

  // --- 移除了 beforeEach ---

  // --- 测试 1：成功路径 ---
  it('should load and display the story elements', async () => {
    
    // 1. 在测试 *内部* 定义模拟
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => MOCK_STORY_DATA,
    });

    render(<App />);

    // 2. 等待 "Kupe and the Octopus" 出现
    //    (findByText 会自动等待 "Loading..." 消失)
    const storyTitle = await screen.findByText(MOCK_STORY_DATA.title);
    
    // 3. 断言
    expect(storyTitle).toBeInTheDocument();
    
    // 4. 验证 "back to menu" 也已渲染
    expect(await screen.findByText(/<-- back to menu/i)).toBeInTheDocument();
    
    // 5. 验证 "Loading..." 消息已经消失
    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
  });

  // --- 测试 2：失败路径 ---
  it('should display an error message if fetch fails', async () => {
    
    // 1. 在测试 *内部* 定义模拟
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
    });

    render(<App />);

    // 2. 等待 "Error loading story:" 出现
    //    (findByText 会自动等待 "Loading..." 消失)
    const errorMessage = await screen.findByText(/Error loading story:/i);

    // 3. 断言
    expect(errorMessage).toBeInTheDocument();

    // 4. 验证 "Loading..." 消息已经消失
    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
  });

});