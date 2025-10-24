// src/setupTests.js
import { expect, afterEach, vi, beforeEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

global.fetch = vi.fn();

afterEach(() => {
  cleanup();
});