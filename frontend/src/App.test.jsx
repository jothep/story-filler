// src/App.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

const MOCK_SUCCESS_DATA = {
  paragraphs: [
    { 
      id: 1, 
      text: 'On a bright moonlit night', 
      audio: 'audio.m4a',
      blank_links: [] 
    }
  ],
  words_in_bank: [
    { 
      id: 1, 
      maori_word: 'kātao', 
      english_translation: 'water'
    }
  ]
};

describe('App Component', () => {

  it('should load and display story content', async () => {
    
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => MOCK_SUCCESS_DATA,
    });

    render(<App />);

    const wordButton = await screen.findByText('kātao');
    
    expect(wordButton).toBeInTheDocument();
    expect(screen.getByText(/On a bright moonlit night/i)).toBeInTheDocument();
    
    expect(screen.queryByText(/^Loading story...$/i)).not.toBeInTheDocument();
  });

  it('should display an error message if fetch fails', async () => {
    
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
    });
    
    vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<App />);

    const errorMessage = await screen.findByText(/Error loading story:/i);
    
    expect(errorMessage).toBeInTheDocument();

    expect(screen.queryByText(/^Loading story...$/i)).not.toBeInTheDocument();
  });
});