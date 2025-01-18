import React, { createContext, useState, useEffect, useCallback } from 'react';

export const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [credits, setCredits] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const API_BASE_URL = 'http://localhost:8000/api';

  const fetchCredits = useCallback(async () => {
    try {
      const accessToken = localStorage.getItem('tokens') ? JSON.parse(localStorage.getItem('tokens')).access : null;
      if (!accessToken) {
        console.error('No access token found');
        setIsLoading(false);
        return;
      }

      const response = await fetch(`${API_BASE_URL}/credits/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch credits');
      }
      
      const data = await response.json();
      if (typeof data.credits === 'number') {
        setCredits(data.credits);
      }
    } catch (error) {
      console.error('Error fetching credits:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCredits();
    // Set up periodic refresh
    const refreshInterval = setInterval(fetchCredits, 5000);
    return () => clearInterval(refreshInterval);
  }, [fetchCredits]);

  return (
    <UserContext.Provider value={{ credits, setCredits, isLoading, fetchCredits }}>
      {children}
    </UserContext.Provider>
  );
}; 