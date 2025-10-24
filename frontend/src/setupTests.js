// src/setupTests.js
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// 1. (可选，但推荐) 使用 stubGlobal 来模拟 fetch
// 这比 global.fetch = vi.fn() 更健壮
vi.stubGlobal('fetch', vi.fn());

// 2. 在每次测试后，
afterEach(() => {
  // a. 清理 jsdom
  cleanup();
  // b. 恢复所有 mock 到它们的原始实现
  vi.restoreAllMocks();
});