import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

// Mock components
jest.mock('./components/Login', () => () => <div>Login</div>);
jest.mock('./components/Register', () => () => <div>Register</div>);
jest.mock('./components/Dashboard', () => () => <div>Dashboard</div>);
jest.mock('./components/SingleGameAnalysis', () => () => <div>SingleGameAnalysis</div>);
jest.mock('./components/BatchAnalysis', () => () => <div>BatchAnalysis</div>);
jest.mock('./components/Credits', () => () => <div>Credits</div>);
jest.mock('./components/FetchGames', () => () => <div>FetchGames</div>);

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
  });

  it('redirects to login when not authenticated', () => {
    mockLocalStorage.getItem.mockReturnValue(null);
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText('Login')).toBeInTheDocument();
  });

  it('shows dashboard when authenticated', () => {
    mockLocalStorage.getItem.mockReturnValue('mock-token');
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('shows register page', () => {
    render(
      <MemoryRouter initialEntries={['/register']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText('Register')).toBeInTheDocument();
  });

  it('shows login page', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText('Login')).toBeInTheDocument();
  });
});
