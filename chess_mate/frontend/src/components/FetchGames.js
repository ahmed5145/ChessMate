import React, { useState } from 'react';
import { Download, CreditCard, AlertCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import { fetchExternalGames } from '../api';

const FetchGames = ({ onGamesFetched }) => {
  const [username, setUsername] = useState('');
  const [platform, setPlatform] = useState('chesscom');
  const [loading, setLoading] = useState(false);
  const [credits, setCredits] = useState(0);

  const fetchCredits = async () => {
    try {
      const response = await fetch('/api/credits');
      const data = await response.json();
      setCredits(data.credits);
    } catch (error) {
      console.error('Error fetching credits:', error);
    }
  };

  React.useEffect(() => {
    fetchCredits();
  }, []);

  const handleFetchGames = async (e) => {
    e.preventDefault();
    if (!username) {
      toast.error('Please enter a username');
      return;
    }

    if (credits <= 0) {
      toast.error('Insufficient credits. Please purchase more credits to fetch games.');
      return;
    }

    setLoading(true);
    try {
      const games = await fetchExternalGames(platform, username);
      
      if (games.length > credits) {
        toast.warning(`You only have ${credits} credits. Only the first ${credits} games will be fetched.`);
      }

      // Deduct credits
      const creditsToDeduct = Math.min(games.length, credits);
      await fetch('/api/credits/deduct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: creditsToDeduct })
      });

      await fetchCredits(); // Refresh credits
      if (onGamesFetched) {
        onGamesFetched();
      }
      toast.success(`Successfully fetched ${games.length} games!`);
    } catch (error) {
      console.error('Error fetching games:', error);
      toast.error('Failed to fetch games. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Fetch Chess Games</h2>
        <div className="flex items-center space-x-2">
          <CreditCard className="w-5 h-5 text-indigo-500" />
          <span className="text-sm font-medium text-gray-700">
            {credits} credits remaining
          </span>
        </div>
      </div>

      {credits === 0 && (
        <div className="mb-4 p-4 bg-yellow-50 rounded-md">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-yellow-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                No credits available
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>Purchase credits to fetch and analyze games.</p>
                <button
                  onClick={() => {/* TODO: Implement redirect to pricing page */}}
                  className="mt-2 text-sm font-medium text-yellow-800 hover:text-yellow-900"
                >
                  View pricing →
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleFetchGames} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Chess Platform
          </label>
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="chesscom">Chess.com</option>
            <option value="lichess">Lichess</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Username
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder={`Enter your ${platform === 'chesscom' ? 'Chess.com' : 'Lichess'} username`}
          />
        </div>

        <button
          type="submit"
          disabled={loading || credits === 0}
          className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
            loading || credits === 0
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
          }`}
        >
          {loading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Fetching games...
            </span>
          ) : (
            <span className="flex items-center">
              <Download className="w-5 h-5 mr-2" />
              Fetch Games
            </span>
          )}
        </button>
      </form>
    </div>
  );
};

export default FetchGames;