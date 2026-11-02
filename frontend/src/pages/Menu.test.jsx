import { act, render, screen, cleanup, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import Menu from './Menu';
import { deferred } from '../testUtils/audio';

const MOCK_STORIES = [
  { id: 1, title: 'Story 1' },
  { id: 2, title: 'Story 2' },
];

const MOCK_CONFIG = {
  menu_bgm: {
    id: 1,
    title: 'Test BGM',
    audio_url: '/media/bgm/Schumann_Fantasy.mp3',
  },
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

beforeEach(() => {
  global.Audio = vi.fn().mockImplementation(function (src) {
    this.src = src;
    this.loop = false;
    this.volume = 1;
    this.play = vi.fn().mockResolvedValue(undefined);
    this.pause = vi.fn();
    return this;
  });
});

const renderComponent = (storiesMock, configMock) => {
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});

  // Mock fetch to handle both /api/stories/ and /api/config/
  vi.mocked(fetch).mockImplementation((url) => {
    if (url.includes('/api/stories/')) {
      return Promise.resolve(storiesMock);
    }
    if (url.includes('/api/config/')) {
      return Promise.resolve(configMock);
    }
    return Promise.reject(new Error('Unknown URL'));
  });

  render(
    <MemoryRouter>
      <Menu />
    </MemoryRouter>
  );
};

describe('Menu Component - BGM Configuration', () => {
  it('creates configured audio when config JSON arrives after the stories', async () => {
    const pendingConfig = deferred();
    const readConfig = vi.fn(() => pendingConfig.promise);
    renderComponent(
      {
        ok: true,
        json: async () => MOCK_STORIES,
      },
      {
        ok: true,
        json: readConfig,
      }
    );

    expect(await screen.findByText('Story 1')).toBeInTheDocument();
    await waitFor(() => expect(readConfig).toHaveBeenCalledTimes(1));
    expect(global.Audio).not.toHaveBeenCalled();

    await act(async () => pendingConfig.resolve(MOCK_CONFIG));

    // URL format depends on VITE_API_URL env var (full URL in dev, relative in prod build)
    await waitFor(() => {
      expect(global.Audio).toHaveBeenCalledTimes(1);
      expect(global.Audio).toHaveBeenCalledWith(
        expect.stringMatching(/\/media\/bgm\/Schumann_Fantasy\.mp3$/)
      );
    });
  });

  it('should handle missing BGM configuration gracefully', async () => {
    renderComponent(
      {
        ok: true,
        json: async () => MOCK_STORIES,
      },
      {
        ok: true,
        json: async () => ({ menu_bgm: null }),
      }
    );

    await waitFor(() => {
      expect(screen.queryByText(/Loading stories.../i)).not.toBeInTheDocument();
    });

    expect(await screen.findByText('Story 1')).toBeInTheDocument();
    expect(await screen.findByText('Story 2')).toBeInTheDocument();
  });

  it('should handle API config fetch failure gracefully', async () => {
    renderComponent(
      {
        ok: true,
        json: async () => MOCK_STORIES,
      },
      {
        ok: false,
      }
    );

    await waitFor(() => {
      expect(screen.queryByText(/Loading stories.../i)).not.toBeInTheDocument();
    });

    expect(await screen.findByText('Story 1')).toBeInTheDocument();
  });

  it('should display stories after loading', async () => {
    renderComponent(
      {
        ok: true,
        json: async () => MOCK_STORIES,
      },
      {
        ok: true,
        json: async () => MOCK_CONFIG,
      }
    );

    await waitFor(() => {
      expect(screen.queryByText(/Loading stories.../i)).not.toBeInTheDocument();
    });

    expect(await screen.findByText('Story 1')).toBeInTheDocument();
    expect(await screen.findByText('Story 2')).toBeInTheDocument();
  });
});
