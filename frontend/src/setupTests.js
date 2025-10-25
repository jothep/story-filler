// src/setupTests.js
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// 1. 全局模拟 'fetch'，以便我们可以在测试中控制它
vi.stubGlobal('fetch', vi.fn());

// 2. 在每次测试后:
afterEach(() => {
  // a. 清理 jsdom
  cleanup();
  // b. 恢复所有 mock，防止测试相互污染
  vi.restoreAllMocks();
});
