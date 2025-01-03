import React, { useEffect, useState } from "react";
import axios from "axios";
import FetchGames from "./FetchGames";

const Dashboard = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchGames = async () => {
    try {
      const response = await axios.get("/api/dashboard/", {
        headers: {
          Authorization: `Bearer ${JSON.parse(localStorage.getItem("tokens")).access}`,
        },
      });
      setGames(response.data.games);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching games:", error);
      setLoading(false);
    }
  };

  const analyzeGame = async (gameId) => {
    try {
      const response = await axios.post(
        `/api/game/${gameId}/analyze/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${JSON.parse(localStorage.getItem("tokens")).access}`,
          },
        }
      );
      alert("Analysis complete! Check analysis results.");
      // Handle the response to update the UI or provide more feedback
      console.log("Analysis response:", response.data);
    } catch (error) {
      alert("Error analyzing game: " + (error.response?.data?.error || error.message));
    }
  };

  useEffect(() => {
    fetchGames();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <FetchGames />
      <h2 className="text-xl font-semibold mt-6 mb-4">Your Games</h2>
      {loading ? (
        <p>Loading games...</p>
      ) : games.length > 0 ? (
        <table className="min-w-full border-collapse border border-gray-300">
          <thead>
            <tr>
              <th className="border border-gray-300 px-4 py-2">Opponent</th>
              <th className="border border-gray-300 px-4 py-2">Result</th>
              <th className="border border-gray-300 px-4 py-2">Played At</th>
              <th className="border border-gray-300 px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {games.map((game) => (
              <tr key={game.id}>
                <td className="border border-gray-300 px-4 py-2">
                  {game.opponent}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {game.result}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {game.played_at ? new Date(game.played_at).toLocaleString() : "Unknown"}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  <button
                    onClick={() => analyzeGame(game.id)}
                    className="px-3 py-1 bg-green-500 text-white rounded-md"
                  >
                    Analyze
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No games found. Fetch games to get started!</p>
      )}
    </div>
  );
};

export default Dashboard;
