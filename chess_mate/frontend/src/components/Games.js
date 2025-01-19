import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Filter, Search } from 'lucide-react';
import { toast } from 'react-hot-toast';

const API_BASE_URL = 'http://localhost:8000/api';

const Games = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, analyzed, unanalyzed
  const [sort, setSort] = useState('date'); // date, result
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchGames();
  }, []);

  const fetchGames = async () => {
    try {
      const accessToken = localStorage.getItem('tokens') ? JSON.parse(localStorage.getItem('tokens')).access : null;
      if (!accessToken) {
        toast.error('Please log in to view your games');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/games/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch games');
      }

      const data = await response.json();
      // Clean up opponent names by removing "vs " prefix if present
      const cleanedGames = data.map(game => ({
        ...game,
        opponent: game.opponent.replace(/^vs\s+/, '')
      }));
      console.log('Fetched games:', cleanedGames);
      setGames(cleanedGames);
    } catch (error) {
      console.error('Error fetching games:', error);
      toast.error('Failed to load games. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filteredGames = games
    .filter(game => {
      // First apply search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return (
          game.opponent.toLowerCase().includes(searchLower) ||
          game.opening_name?.toLowerCase().includes(searchLower) ||
          game.result.toLowerCase().includes(searchLower)
        );
      }
      // Then apply analysis filter
      if (filter === 'analyzed') return game.analysis;
      if (filter === 'unanalyzed') return !game.analysis;
      return true;
    })
    .sort((a, b) => {
      if (sort === 'date') {
        return new Date(b.played_at) - new Date(a.played_at);
      }
      if (sort === 'result') {
        const resultOrder = { win: 0, draw: 1, loss: 2 };
        return resultOrder[a.result.toLowerCase()] - resultOrder[b.result.toLowerCase()];
      }
      return 0;
    });

  const getResultBadgeColor = (result) => {
    const lowerResult = result.toLowerCase();
    switch (lowerResult) {
      case 'win':
        return 'bg-green-100 text-green-800';
      case 'loss':
        return 'bg-red-100 text-red-800';
      case 'draw':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-3xl font-bold text-gray-900">My Games</h1>
          <p className="mt-2 text-sm text-gray-700">
            A list of all your chess games, including their results and analysis status.
            {games.length > 0 && ` Total games: ${games.length}`}
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <Link
            to="/fetch-games"
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            Import Games
          </Link>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mt-8 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -mt-2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search games..."
            className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -mt-2 h-4 w-4 text-gray-400" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="pl-10 block w-full rounded-md border-gray-300 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
          >
            <option value="all">All Games</option>
            <option value="analyzed">Analyzed Games</option>
            <option value="unanalyzed">Unanalyzed Games</option>
          </select>
        </div>
        <div className="relative">
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="block w-full rounded-md border-gray-300 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
          >
            <option value="date">Sort by Date</option>
            <option value="result">Sort by Result</option>
          </select>
        </div>
      </div>

      <div className="mt-8 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            {loading ? (
              <div className="text-center py-12">
                <div className="spinner"></div>
                <p className="mt-4 text-gray-500">Loading games...</p>
              </div>
            ) : filteredGames.length > 0 ? (
              <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                <table className="min-w-full divide-y divide-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">
                        Opponent
                      </th>
                      <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                        Opening
                      </th>
                      <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                        Date
                      </th>
                      <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                        Result
                      </th>
                      <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                        Status
                      </th>
                      <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {filteredGames.map((game) => (
                      <tr key={`${game.id}-${game.played_at}`}>
                        <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                          {game.opponent}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {game.opening_name || 'Unknown Opening'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {new Date(game.played_at).toLocaleDateString()}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${getResultBadgeColor(game.result)}`}>
                            {game.result}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {game.analysis ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Analyzed
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              Not Analyzed
                            </span>
                          )}
                        </td>
                        <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                          <Link
                            to={`/analysis/${game.id}`}
                            className="text-indigo-600 hover:text-indigo-900"
                            onClick={async (e) => {
                              e.preventDefault();
                              const toastId = `analysis-${game.id}`;
                              
                              try {
                                const accessToken = localStorage.getItem('tokens') ? JSON.parse(localStorage.getItem('tokens')).access : null;
                                if (!accessToken) {
                                  toast.error('Please log in to analyze games');
                                  return;
                                }

                                // Show analysis in progress
                                toast.loading('Analyzing game...', { id: toastId });

                                const response = await fetch(`${API_BASE_URL}/game/${game.id}/analysis/`, {
                                  method: 'POST',
                                  headers: {
                                    'Authorization': `Bearer ${accessToken}`,
                                    'Content-Type': 'application/json'
                                  },
                                  body: JSON.stringify({
                                    depth: 20,
                                    use_ai: true
                                  })
                                });

                                const data = await response.json();

                                if (!response.ok) {
                                  toast.error(data.error || 'Failed to analyze game', { id: toastId });
                                  throw new Error(data.error || 'Failed to analyze game');
                                }

                                // Update the game in the local state
                                setGames(prevGames => 
                                  prevGames.map(g => 
                                    g.id === game.id 
                                      ? { ...g, analysis: data.analysis }
                                      : g
                                  )
                                );

                                // Show success message
                                toast.success(data.message || 'Analysis completed!', { id: toastId });

                                // Refresh the games list
                                fetchGames();

                                // Navigate to analysis view
                                window.location.href = `/analysis/${game.id}`;
                              } catch (error) {
                                console.error('Error analyzing game:', error);
                                toast.error(error.message || 'Failed to analyze game', { id: toastId });
                              }
                            }}
                          >
                            View Analysis
                            <span className="sr-only">, game {game.id}</span>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-sm text-gray-500">No games found. Try adjusting your filters or import some games.</p>
                <Link
                  to="/fetch-games"
                  className="mt-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  Import Games
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Games; 