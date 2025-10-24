// src/App.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// (模拟数据保持不变)
const MOCK_SUCCESS_DATA = {
  paragraphs: [
    { 
      id: 1, 
      text: 'On a bright moonlit night', 
      audio: 'audio.m4a',
      blank_links: [] 
    }
  ],
  words_in_bank: [
    { 
      id: 1, 
      maori_word: 'kātao', 
      english_translation: 'water'
    }
  ]
};

describe('App Component', () => {

  // 测试 1: 成功路径 (这个已经通过了, 但我们保持一致)
  it('should load and display story content', async () => {
    
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => MOCK_SUCCESS_DATA,
    });

    render(<App />);

    // 等待 "kātao" 按钮出现
    const wordButton = await screen.findByText('kātao');
    
    // 断言
    expect(wordButton).toBeInTheDocument();
    expect(screen.getByText(/On a bright moonlit night/i)).toBeInTheDocument();
    
    // 关键：在所有 'await' 完成后，再检查“不应该”存在的东西
    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
  });

  // 测试 2: 失败路径 (已修复)
  it('should display an error message if fetch fails', async () => {
    
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
    });
    
    vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<App />);

    // 关键修复：
    // 1. 我们 *只* await 错误消息的 *出现*
    const errorMessage = await screen.findByText(/Error loading story:/i);
    
    // 2. 断言它确实出现了
    expect(errorMessage).toBeInTheDocument();

    // 3. (这是最重要的) 在所有 await *之后*，我们才
    //    同步地检查 "Loading..." 消息是否 *消失* 了。
    //    这能确保 React 有足够的时间完成它的 'setLoading(false)' 批处理。
    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
  });
});