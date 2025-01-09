import React, { useState } from "react";
import { fetchExternalGames } from "../api";
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const FetchGames = ({ onGamesFetched }) => {
  const [username, setUsername] = useState("");
  const [platform, setPlatform] = useState("chess.com");
  const [loading, setLoading] = useState(false);

  const handleFetchGames = async () => {
    setLoading(true);
    if (!username.trim()) {
      toast.error("Username cannot be empty!");
      setLoading(false);
      return;
    }

    try {
      await fetchExternalGames(platform, username);
      toast.success("Games fetched successfully!");
      onGamesFetched();
    } catch (error) {
      console.error("Error fetching games:", error);
      toast.error("Failed to fetch games. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Fetch Your Games</h2>
      <div className="mb-4">
        <label className="block text-sm font-medium">Username:</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring focus:ring-indigo-500"
        />
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium">Platform:</label>
        <select
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring focus:ring-indigo-500"
        >
          <option value="chess.com">Chess.com</option>
          <option value="lichess">Lichess</option>
        </select>
      </div>
      <button
        onClick={handleFetchGames}
        disabled={loading}
        className={`px-4 py-2 bg-indigo-600 text-white rounded-md ${
          loading ? "opacity-50 cursor-not-allowed" : ""
        }`}
      >
        {loading ? "Fetching Games..." : "Fetch Games"}
      </button>
    </div>
  );
};

export default FetchGames;
