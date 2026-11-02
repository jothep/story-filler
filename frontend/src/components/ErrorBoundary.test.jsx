import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import ErrorBoundary from './ErrorBoundary';

function BrokenContent() {
  throw new Error('Example render failure');
}

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => vi.unstubAllEnvs());

describe('error details by build mode', () => {
  it.each([true, false])(
    'limits diagnostics to development (DEV=%s)',
    (dev) => {
      vi.stubEnv('DEV', dev);
      render(
        <ErrorBoundary>
          <BrokenContent />
        </ErrorBoundary>
      );

      expect(screen.getByRole('heading')).toHaveTextContent(
        'Something went wrong'
      );
      expect(
        screen.getByRole('button', { name: 'Return to Home' })
      ).toBeInTheDocument();
      if (dev) {
        expect(
          screen.getByText('Error Details (Dev Mode)')
        ).toBeInTheDocument();
        expect(screen.getByText(/Example render failure/)).toBeInTheDocument();
      } else {
        expect(
          screen.queryByText('Error Details (Dev Mode)')
        ).not.toBeInTheDocument();
        expect(
          screen.queryByText(/Example render failure/)
        ).not.toBeInTheDocument();
      }
    }
  );
});
