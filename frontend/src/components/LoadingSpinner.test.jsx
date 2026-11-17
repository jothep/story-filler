import { render, screen, cleanup } from '@testing-library/react';
import { describe, it, expect, afterEach } from 'vitest';
import LoadingSpinner from './LoadingSpinner';

afterEach(() => {
  cleanup();
});

describe('LoadingSpinner', () => {
  it('shows the message and explains the cold-start wait', () => {
    render(<LoadingSpinner message="Loading stories..." />);

    expect(screen.getByText('Loading stories...')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Waking up the free server. First load can take up to 30s.'
      )
    ).toBeInTheDocument();
  });
});
