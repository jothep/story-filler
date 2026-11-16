import { render, screen, cleanup } from '@testing-library/react';
import { describe, it, expect, afterEach } from 'vitest';
import LoadingSpinner, { COLD_START_NOTE } from './LoadingSpinner';

afterEach(() => {
  cleanup();
});

describe('LoadingSpinner', () => {
  it('shows the message and explains the cold-start wait', () => {
    render(<LoadingSpinner message="Loading stories..." />);

    expect(screen.getByText('Loading stories...')).toBeInTheDocument();
    expect(screen.getByText(COLD_START_NOTE)).toBeInTheDocument();
    expect(COLD_START_NOTE).toMatch(/up to \d+s\./);
  });
});
