import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { UserContext } from '../../contexts/UserContext';
import Games from '../Games';
import { toast } from 'react-hot-toast';

// Mock react-hot-toast
jest.mock('react-hot-toast');

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('Games Component', () => {
  const mockGames = [
    {
      id: 1,
      opponent: 'opponent1',
      result: 'win',
      played_at: '2024-01-01T12:00:00Z',
      game_url: 'https://chess.com/game/1',
      opening_name: 'Sicilian Defense',
      is_white: true,
    },
    {
      id: 2,
      opponent: 'opponent2',
      result: 'loss',
      played_at: '2024-01-02T12:00:00Z',
      game_url: 'https://chess.com/game/2',
      opening_name: 'Queens Gambit',
      is_white: false,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockReset();
  });

  test('renders games list', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockGames),
    });

    render(
      <BrowserRouter>
        <UserContext.Provider value={{ credits: 100 }}>
          <Games />
        </UserContext.Provider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/opponent1/i)).toBeInTheDocument();
      expect(screen.getByText(/opponent2/i)).toBeInTheDocument();
      expect(screen.getByText(/Sicilian Defense/i)).toBeInTheDocument();
      expect(screen.getByText(/Queens Gambit/i)).toBeInTheDocument();
    });
  });

  test('handles game mode filter', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockGames),
    });

    render(
      <BrowserRouter>
        <UserContext.Provider value={{ credits: 100 }}>
          <Games />
        </UserContext.Provider>
      </BrowserRouter>
    );

    const filterSelect = screen.getByLabelText(/game mode/i);
    fireEvent.change(filterSelect, { target: { value: 'blitz' } });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('game_mode=blitz'),
        expect.any(Object)
      );
    });
  });

  test('handles fetch error', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ error: 'Failed to fetch games' }),
    });

    render(
      <BrowserRouter>
        <UserContext.Provider value={{ credits: 100 }}>
          <Games />
        </UserContext.Provider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to fetch games');
    });
  });

  test('displays loading state', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <BrowserRouter>
        <UserContext.Provider value={{ credits: 100 }}>
          <Games />
        </UserContext.Provider>
      </BrowserRouter>
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('handles analyze game click', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockGames),
    });

    render(
      <BrowserRouter>
        <UserContext.Provider value={{ credits: 100 }}>
          <Games />
        </UserContext.Provider>
      </BrowserRouter>
    );

    await waitFor(() => {
      const analyzeButtons = screen.getAllByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButtons[0]);
      expect(mockNavigate).toHaveBeenCalledWith('/analysis/1');
    });
  });
}); 