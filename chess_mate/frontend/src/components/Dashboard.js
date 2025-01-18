import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { UserContext } from '../contexts/UserContext';
import { ChevronRight, PieChart, Clock, Target, Award } from 'lucide-react';
import { toast } from 'react-hot-toast';

const API_BASE_URL = 'http://localhost:8000/api';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { credits } = useContext(UserContext);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const accessToken = localStorage.getItem('tokens') ? JSON.parse(localStorage.getItem('tokens')).access : null;
      if (!accessToken) {
        toast.error('Please log in to view your dashboard');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/dashboard/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-700">
          Welcome back! You have {credits} credits available.
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <PieChart className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Games</dt>
                  <dd className="text-lg font-medium text-gray-900">{dashboardData?.total_games || 0}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Target className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Win Rate</dt>
                  <dd className="text-lg font-medium text-gray-900">{dashboardData?.statistics?.win_rate || 0}%</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Award className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Analyzed Games</dt>
                  <dd className="text-lg font-medium text-gray-900">{dashboardData?.analyzed_games || 0}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Pending Analysis</dt>
                  <dd className="text-lg font-medium text-gray-900">{dashboardData?.unanalyzed_games || 0}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Games */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-900">Recent Games</h2>
          <Link
            to="/games"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-500 flex items-center"
          >
            View all games
            <ChevronRight className="ml-1 h-4 w-4" />
          </Link>
        </div>
        <div className="border-t border-gray-200">
          {dashboardData?.recent_games?.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {dashboardData.recent_games.map((game) => (
                <li key={game.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                  <Link to={`/game/${game.id}/analysis`} className="flex justify-between items-center">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        vs {game.opponent}
                      </p>
                      <p className="text-sm text-gray-500">
                        {new Date(game.played_at).toLocaleDateString()} • {game.opening_name || 'Unknown Opening'}
                      </p>
                    </div>
                    <div className="flex items-center">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          game.result.toLowerCase() === 'win'
                            ? 'bg-green-100 text-green-800'
                            : game.result.toLowerCase() === 'loss'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {game.result}
                      </span>
                      <ChevronRight className="ml-4 h-5 w-5 text-gray-400" />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-6">
              <p className="text-sm text-gray-500">No games found. Import some games to get started!</p>
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
  );
};

export default Dashboard;