// src/App.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// 1. 创建一个最小化的模拟数据
//    这只需要包含你的组件渲染所需的 *最小* 字段
const MOCK_SUCCESS_DATA = {
  // 'paragraphs' 字段是必须的，以防止 'paragraphs.map' 错误
  paragraphs: [
    { 
      id: 1, 
      text: 'On a bright moonlit night', // 文本，用于断言
      blank_links: [] 
    }
  ],
  // 'words_in_bank' 字段是必须的
  words_in_bank: [
    { 
      id: 1, 
      maori_word: 'kātao' // 文本，用于断言
    }
  ]
};

// --- 开始测试套件 ---
describe('App Component', () => {

  // 测试 1: 成功路径
  it('should load and display story content', async () => {
    
    // 模拟一个成功的 fetch
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => MOCK_SUCCESS_DATA,
    });

    render(<App />);

    // 断言："Loading..." 消息首先出现
    expect(screen.getByText(/Loading story.../i)).toBeInTheDocument();

    // 关键：等待异步操作完成。
    // 我们等待 "kātao" (来自 words_in_bank) 的按钮出现
    const wordButton = await screen.findByText('kātao');

    // 断言：
    // 1. 单词按钮现在在 DOM 中
    expect(wordButton).toBeInTheDocument();
    // 2. 段落文本也在 DOM 中
    expect(screen.getByText(/On a bright moonlit night/i)).toBeInTheDocument();
    // 3. "Loading..." 消息现在 *消失* 了
    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
  });

  // 测试 2: 失败路径
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

    // 关键：等待 "Error..." 消息出现
    const errorMessage = await screen.findByText(/Error loading story:/i);
    
    // 断言：
    // 1. 错误消息现在在 DOM 中
    expect(errorMessage).toBeInTheDocument();
    // 2. "Loading..." 消息现在 *消失* 了
    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
  });
});