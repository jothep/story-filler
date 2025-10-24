// src/App.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import App from './App';

// --- 这是我们将模拟的 API 响应 ---
// 它必须包含你的组件需要的所有数据，以防止 '...of undefined' 错误
const MOCK_STORY_DATA = {
  id: 3,
  title: 'Kupe and the Octopus', // <-- 测试正在寻找这个标题
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
          word: { id: 1, maori_word: 'test' /* ... */ }
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

// --- 描述我们的测试套件 ---
describe('App Component', () => {

  // 在 *每次* 测试运行前，重置我们的 fetch 模拟
  beforeEach(() => {
    // 必须重置模拟，否则测试会相互干扰
    vi.mocked(fetch).mockReset();
  });

  // --- 修复后的测试 1：测试加载和显示 ---
  it('should load and display the story elements', async () => {
    
    // 1. 模拟一个 *成功* 的 fetch 响应
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => MOCK_STORY_DATA,
    });

    // 2. 渲染 App
    render(<App />);

    // 3. (可选) 我们可以先验证 "Loading" 状态
    expect(screen.getByText(/Loading story.../i)).toBeInTheDocument();

    // 4. (关键) 使用 "await findBy..." 来等待 UI 更新
    // 这会自动处理 'act(...)' 警告
    const storyTitle = await screen.findByText(MOCK_STORY_DATA.title);
    
    // 5. 断言
    expect(storyTitle).toBeInTheDocument();
    
    // 6. 验证 "Loading..." 消息已经消失
    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
    
    // 7. 验证其他部分也已渲染
    // (我们从 "Māori Story-Fill" 改为 "back to menu"，
    // 因为这是你的 TopNav 组件实际渲染的内容)
    expect(await screen.findByText(/<-- back to menu/i)).toBeInTheDocument();
  });

  // --- 修复后的测试 2：测试错误状态 ---
  it('should display an error message if fetch fails', async () => {
    
    // 1. 模拟一个 *失败* 的 fetch 响应
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
    });

    // 2. 渲染 App
    render(<App />);

    // 3. (可选) 验证 "Loading" 状态
    expect(screen.getByText(/Loading story.../i)).toBeInTheDocument();

    // 4. (关键) 等待错误消息出现
    const errorMessage = await screen.findByText(/Error loading story:/i);

    // 5. 断言
    expect(errorMessage).toBeInTheDocument();
    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
  });

});