import React, { useEffect, useState } from "react";
import { analyzeSpecificGame, fetchUserGames } from "../api";
import FetchGames from "./FetchGames";

const Dashboard = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const gamesPerPage = 10;

  const fetchGames = async () => {
    setLoading(true);
    try {
      const data = await fetchUserGames({ withCredentials: true });
      setGames(data);
    } catch (error) {
      console.error("Error fetching games:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGames();
  }, []);

  const indexOfLastGame = currentPage * gamesPerPage;
  const indexOfFirstGame = indexOfLastGame - gamesPerPage;
  const currentGames = games.slice(indexOfFirstGame, indexOfLastGame);

  const totalPages = Math.ceil(games.length / gamesPerPage);

  const renderPageButtons = () => {
    const buttons = [];
    const maxVisiblePages = 5;

    if (currentPage > 1) {
      buttons.push(
        <button
          key="first"
          onClick={() => setCurrentPage(1)}
          className="px-3 py-1 mx-1 bg-gray-300 text-black rounded-md"
        >
          First
        </button>
      );
    }

    const startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    for (let i = startPage; i <= endPage; i++) {
      buttons.push(
        <button
          key={i}
          onClick={() => setCurrentPage(i)}
          className={`px-3 py-1 mx-1 rounded-md ${
            currentPage === i
              ? "bg-indigo-600 text-white"
              : "bg-gray-300 text-black"
          }`}
        >
          {i}
        </button>
      );
    }

    if (currentPage < totalPages) {
      buttons.push(
        <button
          key="last"
          onClick={() => setCurrentPage(totalPages)}
          className="px-3 py-1 mx-1 bg-gray-300 text-black rounded-md"
        >
          Last
        </button>
      );
    }

    return buttons;
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <FetchGames onGamesFetched={fetchGames} />
      <h2 className="text-xl font-semibold mt-6 mb-4">Your Games</h2>
      {loading ? (
        <p>Loading games...</p>
      ) : games.length > 0 ? (
        <div>
          <table className="min-w-full border-collapse border border-gray-300">
            <thead>
              <tr>
                <th className="border border-gray-300 px-4 py-2">Result</th>
                <th className="border border-gray-300 px-4 py-2">Pieces</th>
                <th className="border border-gray-300 px-4 py-2">Played At</th>
                <th className="border border-gray-300 px-4 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentGames.map((game) => (
                <tr key={game.id}>
                  <td className="border border-gray-300 px-4 py-2">
                    {game.result || "Unknown"}
                  </td>
                  <td className="border border-gray-300 px-4 py-2">
                    {game.is_white === true || game.is_white === 1 ? "White" : "Black"}
                  </td>
                  <td className="border border-gray-300 px-4 py-2">
                    {game.played_at
                      ? new Date(game.played_at).toLocaleString()
                      : "Unknown"}
                  </td>
                  <td className="border border-gray-300 px-4 py-2">
                    <button
                      onClick={() => analyzeSpecificGame(game.id)}
                      className="px-3 py-1 bg-green-500 text-white rounded-md"
                    >
                      Analyze
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-4 flex justify-center">{renderPageButtons()}</div>
        </div>
      ) : (
        <p>No games found. Fetch games to get started!</p>
      )}
    </div>
  );
};

export default Dashboard;
