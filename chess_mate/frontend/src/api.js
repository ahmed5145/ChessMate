import axios from "axios";

// Set the base URL for API requests
const API_BASE_URL = "http://localhost:8000/api"; // Update if needed for deployment

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
    const response = await api.post("/login/", credentials);
    const { access } = response.data.tokens;
    setAuthHeader(access); // Set the auth header for future requests
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
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
    const response = await api.post(`/game/${gameId}/analyze/`);
    return response.data.analysis;
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
export const logoutUser = () => {
  setAuthHeader(null);
};