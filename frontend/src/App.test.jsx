// src/App.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// 1. 创建一个最小化的模拟数据
//    (我们不需要 'title'，因为它没有被渲染)
const MOCK_SUCCESS_DATA = {
  paragraphs: [
    { 
      id: 1, 
      text: 'On a bright moonlit night', // <-- 我们将测试这个
      audio: 'audio.m4a',
      blank_links: [] 
    }
  ],
  words_in_bank: [
    { 
      id: 1, 
      maori_word: 'kātao', // <-- 我们也将测试这个
      english_translation: 'water'
    }
  ]
};

// --- 开始测试套件 ---
describe('App Component', () => {

  // 测试 1: 成功路径 (已修复)
  it('should load and display story content', async () => {
    
    // 模拟一个成功的 fetch
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => MOCK_SUCCESS_DATA,
    });

    render(<App />);

    // 断言："Loading..." 消息首先出现
    expect(screen.getByText(/Loading story.../i)).toBeInTheDocument();

    // 关键修复：
    // 我们不再等待 "Kupe and the Octopus" (不存在的)
    // 而是等待 "kātao" (来自 words_in_bank) 按钮出现
    const wordButton = await screen.findByText('kātao');

    // 断言：
    // 1. 单词按钮现在在 DOM 中
    expect(wordButton).toBeInTheDocument();
    // 2. 段落文本也在 DOM 中 (来自 paragraphs)
    expect(screen.getByText(/On a bright moonlit night/i)).toBeInTheDocument();
    // 3. "Loading..." 消息现在 *消失* 了
    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
  });

  // 测试 2: 失败路径 (已修复)
  it('should display an error message if fetch fails', async () => {
    
    // 模拟一个失败的 fetch
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
    });
    
    // 压制测试日志中预期的 'Network response...' 错误
    vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<App />);

    // 断言： "Loading..." 消息首先出现
    expect(screen.getByText(/Loading story.../i)).toBeInTheDocument();

    // 关键修复：
    // 我们使用 waitFor 来等待 *两个* 条件都满足
    // 这可以防止在状态转换期间出现竞争条件
    await waitFor(() => {
      // 1. 错误消息 *出现*
      expect(screen.getByText(/Error loading story:/i)).toBeInTheDocument();
      // 2. "Loading..." 消息 *消失*
      expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
    });
  });
});