import React, { useState } from "react";
import { fetchExternalGames, fetchAllGames } from "../api";
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const FetchGames = (onGamesFetched) => {
  const [username, setUsername] = useState("");
  const [platform, setPlatform] = useState("chess.com");
  const [games, setGames] = useState([]); // State to hold fetched games
  const [loading, setLoading] = useState(false);

  const handleFetchGames = async () => {
    setLoading(true);
    if (!username.trim()) {
      toast.error("Username cannot be empty!");
      setLoading(false);
      return;
    }

    try {
      const response = await fetchExternalGames(
        "api/fetch-games/",
        { username, platform },
        { withCredentials: true }
      );

      toast.success(response.message || "Games fetched successfully!");

      // Notify parent component about the fetch
      if (onGamesFetched) {
        onGamesFetched();
      }

      // Fetch games from the backend after saving
      const res = await fetchAllGames("api/games/");
      const data = await res.json();
      setGames(data); // Update games state with fetched games
    } catch (error) {
      console.error("Error fetching games:", error);
      toast.error(
        error.response?.data?.error || "Failed to fetch games. Please try again."
      );
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
        className={`px-4 py-2 bg-indigo-600 text-white rounded-md ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        {loading ? "Fetching Games..." : "Fetch Games"}
      </button>

      {/* Display fetched games */}
      {games.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-2">Fetched Games:</h3>
          <table className="table-auto border-collapse border border-gray-400 w-full">
            <thead>
              <tr>
                <th className="border border-gray-300 px-4 py-2">Opponent</th>
                <th className="border border-gray-300 px-4 py-2">Result</th>
                <th className="border border-gray-300 px-4 py-2">Played At</th>
                <th className="border border-gray-300 px-4 py-2">Game URL</th>
              </tr>
            </thead>
            <tbody>
              {games.map((game, index) => (
                <tr key={index}>
                  <td className="border border-gray-300 px-4 py-2">{game.opponent}</td>
                  <td className="border border-gray-300 px-4 py-2">{game.result}</td>
                  <td className="border border-gray-300 px-4 py-2">{new Date(game.played_at).toLocaleString()}</td>
                  <td className="border border-gray-300 px-4 py-2">
                    <a
                      href={game.game_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      View Game
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default FetchGames;
