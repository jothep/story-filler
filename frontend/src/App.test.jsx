// src/App.test.jsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

beforeEach(() => {
  vi.spyOn(global, 'fetch').mockImplementation(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve([
        { id: 1, title: 'Kupe and the Octopus' },
        { id: 2, title: 'Māui and the Sun' },
      ]),
    })
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('App', () => {
  it('should render the main header', () => {
    render(<App />);
    expect(screen.getByText(/Māori Story-Fill/i)).toBeInTheDocument();
  });

  it('should load and display stories', async () => {
    render(<App />);

    const storyTitle = await screen.findByText(/Kupe and the Octopus/i);

    expect(storyTitle).toBeInTheDocument();
    expect(screen.getByText(/Māui and the Sun/i)).toBeInTheDocument();

    expect(screen.queryByText(/Loading story.../i)).not.toBeInTheDocument();
  });
});