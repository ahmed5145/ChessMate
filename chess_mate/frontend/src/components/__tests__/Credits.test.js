import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { UserContext } from '../../contexts/UserContext';
import Credits from '../Credits';
import { toast } from 'react-hot-toast';

// Mock react-hot-toast
jest.mock('react-hot-toast');

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('Credits Component', () => {
  const mockSetCredits = jest.fn();
  const defaultProps = {
    credits: 100,
    setCredits: mockSetCredits,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockReset();
  });

  test('renders credit packages', () => {
    render(
      <BrowserRouter>
        <UserContext.Provider value={defaultProps}>
          <Credits />
        </UserContext.Provider>
      </BrowserRouter>
    );

    expect(screen.getByText(/Basic Package/i)).toBeInTheDocument();
    expect(screen.getByText(/Pro Package/i)).toBeInTheDocument();
    expect(screen.getByText(/Premium Package/i)).toBeInTheDocument();
  });

  test('displays current credits', () => {
    render(
      <BrowserRouter>
        <UserContext.Provider value={defaultProps}>
          <Credits />
        </UserContext.Provider>
      </BrowserRouter>
    );

    expect(screen.getByText(/100 credits/i)).toBeInTheDocument();
  });

  test('handles successful purchase initiation', async () => {
    const mockResponse = {
      ok: true,
      json: () => Promise.resolve({ checkout_url: 'https://stripe.com/checkout' }),
    };
    fetch.mockResolvedValueOnce(mockResponse);

    render(
      <BrowserRouter>
        <UserContext.Provider value={defaultProps}>
          <Credits />
        </UserContext.Provider>
      </BrowserRouter>
    );

    // Find and click the purchase button for the Basic package
    const purchaseButtons = screen.getAllByRole('button', { name: /purchase/i });
    fireEvent.click(purchaseButtons[0]); // Basic package button

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/purchase-credits/',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': expect.any(String),
          }),
        })
      );
    });
  });

  test('handles purchase error', async () => {
    const mockResponse = {
      ok: false,
      status: 400,
      json: () => Promise.resolve({ error: 'Purchase failed' }),
    };
    fetch.mockResolvedValueOnce(mockResponse);

    render(
      <BrowserRouter>
        <UserContext.Provider value={defaultProps}>
          <Credits />
        </UserContext.Provider>
      </BrowserRouter>
    );

    const purchaseButtons = screen.getAllByRole('button', { name: /purchase/i });
    fireEvent.click(purchaseButtons[0]); // Basic package button

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Purchase failed');
    });
  });

  test('updates credits display when credits change', () => {
    const { rerender } = render(
      <BrowserRouter>
        <UserContext.Provider value={defaultProps}>
          <Credits />
        </UserContext.Provider>
      </BrowserRouter>
    );

    expect(screen.getByText(/100 credits/i)).toBeInTheDocument();

    rerender(
      <BrowserRouter>
        <UserContext.Provider value={{ ...defaultProps, credits: 200 }}>
          <Credits />
        </UserContext.Provider>
      </BrowserRouter>
    );

    expect(screen.getByText(/200 credits/i)).toBeInTheDocument();
  });
}); 