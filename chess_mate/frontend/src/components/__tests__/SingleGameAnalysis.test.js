import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import SingleGameAnalysis from '../SingleGameAnalysis';
import { analyzeSpecificGame } from '../../api';

// Mock the API call
jest.mock('../../api', () => ({
  analyzeSpecificGame: jest.fn(),
}));

// Mock chart.js to avoid canvas errors
jest.mock('react-chartjs-2', () => ({
  Line: () => null,
}));

const mockAnalysisData = {
  analysis: [
    {
      move_number: 1,
      move: 'e4',
      score: 0.3,
      time_spent: 5,
      is_critical: false,
      is_check: false,
    },
  ],
  feedback: {
    accuracy: 0.85,
    mistakes: 1,
    blunders: 0,
    time_management: {
      avg_time_per_move: 10,
      suggestion: 'Good time management',
    },
    tactical_opportunities: ['Missed fork on move 15'],
    opening: {
      suggestion: 'Consider developing knights before bishops',
    },
    endgame: {
      suggestion: 'Practice rook endgames',
    },
  },
  game_info: {
    played_at: new Date().toISOString(),
  },
};

describe('SingleGameAnalysis', () => {
  beforeEach(() => {
    analyzeSpecificGame.mockReset();
  });

  it('renders loading state initially', () => {
    analyzeSpecificGame.mockImplementation(() => new Promise(() => {}));

    render(
      <MemoryRouter initialEntries={['/analysis/1']}>
        <Routes>
          <Route path="/analysis/:gameId" element={<SingleGameAnalysis />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Analyzing Game...')).toBeInTheDocument();
  });

  it('renders analysis data when loaded', async () => {
    analyzeSpecificGame.mockResolvedValue(mockAnalysisData);

    render(
      <MemoryRouter initialEntries={['/analysis/1']}>
        <Routes>
          <Route path="/analysis/:gameId" element={<SingleGameAnalysis />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Game Analysis')).toBeInTheDocument();
    });

    expect(screen.getByText('85.0%')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // mistakes
    expect(screen.getByText('0')).toBeInTheDocument(); // blunders
  });

  it('renders error state when API call fails', async () => {
    analyzeSpecificGame.mockRejectedValue(new Error('API Error'));

    render(
      <MemoryRouter initialEntries={['/analysis/1']}>
        <Routes>
          <Route path="/analysis/:gameId" element={<SingleGameAnalysis />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to analyze game. Please try again.')).toBeInTheDocument();
    });
  });

  it('switches between overview and move list tabs', async () => {
    analyzeSpecificGame.mockResolvedValue(mockAnalysisData);

    render(
      <MemoryRouter initialEntries={['/analysis/1']}>
        <Routes>
          <Route path="/analysis/:gameId" element={<SingleGameAnalysis />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Game Analysis')).toBeInTheDocument();
    });

    // Click on Move List tab
    userEvent.click(screen.getByText('Move List'));
    expect(screen.getByText('e4')).toBeInTheDocument();

    // Click back to Overview tab
    userEvent.click(screen.getByText('Overview'));
    expect(screen.getByText('Game Statistics')).toBeInTheDocument();
  });
}); 