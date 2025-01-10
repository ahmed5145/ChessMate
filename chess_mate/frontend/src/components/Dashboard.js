import React, { useEffect, useState } from "react";
import { analyzeSpecificGame, fetchUserGames } from "../api";
import FetchGames from "./FetchGames";
import { ChevronLeft, ChevronRight, Activity } from "lucide-react";

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

  const getResultColor = (result) => {
    switch (result?.toLowerCase()) {
      case "win":
        return "text-green-600";
      case "loss":
        return "text-red-600";
      case "draw":
        return "text-yellow-600";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="sm:flex sm:items-center sm:justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Chess Games Dashboard</h1>
        </div>

        <div className="mt-8 bg-white rounded-lg shadow">
          <div className="p-6">
            <FetchGames onGamesFetched={fetchGames} />
          </div>
        </div>

        <div className="mt-8 bg-white rounded-lg shadow overflow-hidden">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Your Games History</h2>
          </div>

          {loading ? (
            <div className="p-8 flex justify-center">
              <div className="flex items-center space-x-2">
                <svg className="animate-spin h-5 w-5 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-gray-600">Loading games...</span>
              </div>
            </div>
          ) : games.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Result</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pieces</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Played At</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {currentGames.map((game) => (
                      <tr key={game.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getResultColor(game.result)}`}>
                            {game.result || "Unknown"}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {game.is_white === true || game.is_white === 1 ? "White" : "Black"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {game.played_at
                            ? new Date(game.played_at).toLocaleString()
                            : "Unknown"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => analyzeSpecificGame(game.id)}
                            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                          >
                            <Activity className="h-4 w-4 mr-1.5" />
                            Analyze
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                  <div className="flex-1 flex justify-center">
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                      <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                        className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${
                          currentPage === 1
                            ? "text-gray-300 cursor-not-allowed"
                            : "text-gray-500 hover:bg-gray-50"
                        }`}
                      >
                        <ChevronLeft className="h-5 w-5" />
                      </button>
                      {Array.from({ length: totalPages }, (_, i) => i + 1)
                        .filter(page => {
                          const buffer = 2;
                          return page === 1 || 
                                 page === totalPages || 
                                 (page >= currentPage - buffer && 
                                  page <= currentPage + buffer);
                        })
                        .map((page, index, array) => {
                          if (index > 0 && array[index - 1] !== page - 1) {
                            return [
                              <span key={`ellipsis-${page}`} className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                                ...
                              </span>,
                              <button
                                key={page}
                                onClick={() => setCurrentPage(page)}
                                className={`relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium ${
                                  currentPage === page
                                    ? "z-10 bg-indigo-50 border-indigo-500 text-indigo-600"
                                    : "bg-white text-gray-500 hover:bg-gray-50"
                                }`}
                              >
                                {page}
                              </button>
                            ];
                          }
                          return (
                            <button
                              key={page}
                              onClick={() => setCurrentPage(page)}
                              className={`relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium ${
                                currentPage === page
                                  ? "z-10 bg-indigo-50 border-indigo-500 text-indigo-600"
                                  : "bg-white text-gray-500 hover:bg-gray-50"
                              }`}
                            >
                              {page}
                            </button>
                          );
                        })}
                      <button
                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage === totalPages}
                        className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${
                          currentPage === totalPages
                            ? "text-gray-300 cursor-not-allowed"
                            : "text-gray-500 hover:bg-gray-50"
                        }`}
                      >
                        <ChevronRight className="h-5 w-5" />
                      </button>
                    </nav>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No games found. Fetch games to get started!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;