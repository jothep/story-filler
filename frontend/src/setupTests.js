import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Each test supplies its own API responses.
vi.stubGlobal('fetch', vi.fn());

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
