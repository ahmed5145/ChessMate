import React, { useState } from "react";
import { fetchExternalGames } from "../api";
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const FetchGames = ({ onGamesFetched }) => {
  const [username, setUsername] = useState("");
  const [platform, setPlatform] = useState("chess.com");
  const [gameType, setGameType] = useState("rapid"); // Changed default to "rapid"
  const [loading, setLoading] = useState(false);

  const handleFetchGames = async () => {
    setLoading(true);
    if (!username.trim()) {
      toast.error("Username cannot be empty!");
      setLoading(false);
      return;
    }

    try {
      const response = await fetchExternalGames(platform, username, gameType);
      toast.success(response.message);
      if (onGamesFetched) {
        onGamesFetched();
      }
    } catch (error) {
      console.error("Error fetching games:", error);
      toast.error(error.message || "Failed to fetch games. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Fetch Your Games</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Username:
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Platform:
          </label>
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="chess.com">Chess.com</option>
            <option value="lichess">Lichess</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Game Type:
          </label>
          <select
            value={gameType}
            onChange={(e) => setGameType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="bullet">Bullet</option>
            <option value="blitz">Blitz</option>
            <option value="rapid">Rapid</option>
            <option value="classical">Classical</option>
          </select>
        </div>

        <button
          onClick={handleFetchGames}
          disabled={loading}
          className={`w-full px-4 py-2 text-white bg-indigo-600 rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors
            ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Fetching Games...
            </span>
          ) : (
            "Fetch Games"
          )}
        </button>
      </div>
    </div>
  );
};

export default FetchGames;