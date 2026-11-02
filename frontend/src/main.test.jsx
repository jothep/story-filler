import { afterEach, expect, it, vi } from 'vitest';

afterEach(() => vi.restoreAllMocks());

it('reports a missing mount element before starting React', async () => {
  vi.spyOn(document, 'getElementById').mockReturnValue(null);

  await expect(import('./main.jsx')).rejects.toThrow(
    'The application root element is missing.'
  );
});
