import axios from "axios";
import { jwtDecode } from "jwt-decode";

// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Configure axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Helper function to add the Authorization header if the user is authenticated
const setAuthHeader = (token) => {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
};

// Helper function to check if the user is online
const isUserOnline = () => {
  return navigator.onLine;
};

// Helper function to remove tokens if they are expired and the user is not online
const removeExpiredTokens = () => {
  const accessToken = localStorage.getItem("access_token");
  const refreshToken = localStorage.getItem("refresh_token");

  if (accessToken) {
    const decodedAccessToken = jwtDecode(accessToken);
    const currentTime = Date.now() / 1000;

    if (decodedAccessToken.exp < currentTime && !isUserOnline()) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      setAuthHeader(null);
    }
  }

  if (refreshToken) {
    const decodedRefreshToken = jwtDecode(refreshToken);
    const currentTime = Date.now() / 1000;

    if (decodedRefreshToken.exp < currentTime && !isUserOnline()) {
      localStorage.removeItem("refresh_token");
    }
  }
};

// Call removeExpiredTokens on script load
removeExpiredTokens();

// Refresh the access token
export const refreshToken = async (refreshToken) => {
  try {
    const response = await api.post("/token/refresh/", { refresh: refreshToken });
    const { access } = response.data;
    setAuthHeader(access); // Set the new access token
    localStorage.setItem("access_token", access); // Update the access token in local storage
    return access;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

// Interceptor to refresh token if it's about to expire
api.interceptors.request.use(
  async (config) => {
    const accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");

    if (accessToken) {
      const decodedToken = jwtDecode(accessToken);
      const currentTime = Date.now() / 1000;

      // Check if the token is about to expire (e.g., within 5 minutes)
      if (decodedToken.exp - currentTime < 300) {
        const newAccessToken = await refreshToken(refreshToken);
        config.headers["Authorization"] = `Bearer ${newAccessToken}`;
      } else {
        config.headers["Authorization"] = `Bearer ${accessToken}`;
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// API functions

// Register a new user
export const registerUser = async (userData) => {
  try {
    const response = await api.post("/register/", userData);
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

// Login a user
export const loginUser = async (credentials) => {
  try {
    // Remove existing tokens before attempting to login
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setAuthHeader(null);

    const response = await api.post("/login/", credentials);
    const { tokens } = response.data;
    
    if (!tokens || !tokens.access || !tokens.refresh) {
      throw new Error("Invalid response from server");
    }
    
    setAuthHeader(tokens.access); // Set the auth header for future requests
    localStorage.setItem("access_token", tokens.access); // Store the access token
    localStorage.setItem("refresh_token", tokens.refresh); // Store the refresh token
    localStorage.setItem("tokens", JSON.stringify(tokens)); // Store the full tokens object
    return response.data;
  } catch (error) {
    if (error.response) {
      throw error.response.data;
    }
    throw { error: error.message || "Login failed" };
  }
};

// Fetch games for the authenticated user
export const fetchUserGames = async () => {
  try {
    const response = await api.get("/dashboard/");
    return response.data.games;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

// Fetch games from an external platform
export const fetchExternalGames = async (platform, username, gameType) => {
  try {
    // Handle "all" game type by using "rapid" as default
    const effectiveGameType = gameType === "all" ? "rapid" : gameType;
    
    const response = await api.post("/fetch-games/", {
      platform,
      username,
      game_type: effectiveGameType
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

// Analyze a specific game
export const analyzeSpecificGame = async (gameId) => {
  try {
    const response = await api.post(`/game/${gameId}/analysis/`);
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

// Analyze a batch of games
export const analyzeBatchGames = async (numGames) => {
  try {
    const response = await api.post("/games/batch-analyze/", { num_games: parseInt(numGames, 10) });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

// Fetch analysis for a game
export const fetchGameAnalysis = async (gameId) => {
  try {
    const response = await api.get(`/game/${gameId}/analysis/`);
    return response.data.analysis;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

// Fetch feedback for a specific game
export const fetchGameFeedback = async (gameId) => {
  try {
    const response = await api.get(`/feedback/${gameId}/`);
    return response.data.feedback;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

// Fetch all available games
export const fetchAllGames = async () => {
  try {
    const response = await api.get("/games/");
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

// Log out the user
export const logoutUser = async () => {
  try {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      await api.post("/logout/", { refresh_token: refreshToken });
    }
  } catch (error) {
    console.error("Error logging out:", error);
  } finally {
    setAuthHeader(null);
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("tokens");
  }
};

export const requestPasswordReset = async (email) => {
  const response = await fetch(`${API_BASE_URL}/auth/password-reset/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Failed to request password reset");
  }
  return data;
};

export const resetPassword = async (uid, token, newPassword) => {
  const response = await fetch(`${API_BASE_URL}/auth/password-reset/confirm/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ uid, token, new_password: newPassword }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Failed to reset password");
  }
  return data;
};

const getToken = () => {
  const tokens = localStorage.getItem('tokens');
  if (!tokens) {
    throw new Error('No authentication token found');
  }
  return JSON.parse(tokens).access;
};

export const getUserProfile = async () => {
  const response = await fetch(`${API_BASE_URL}/profile/`, {
    headers: {
      'Authorization': `Bearer ${getToken()}`,
    },
  });

  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || 'Failed to fetch profile');
    error.status = response.status;
    throw error;
  }
  return data;
};

export const updateUserProfile = async (profileData) => {
  const response = await fetch(`${API_BASE_URL}/profile/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`,
    },
    body: JSON.stringify(profileData),
  });

  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || 'Failed to update profile');
    error.status = response.status;
    throw error;
  }
  return data;
};
