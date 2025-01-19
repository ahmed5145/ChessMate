import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { Loader2 } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

const BatchAnalysis = () => {
  const [numGames, setNumGames] = useState(10);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [results, setResults] = useState(null);
  const [estimatedTime, setEstimatedTime] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime, setStartTime] = useState(null);

  useEffect(() => {
    let timer;
    if (startTime && loading) {
      timer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        setElapsedTime(elapsed);
        
        // Update estimated time based on current progress
        if (progress.current > 0) {
          const timePerGame = elapsed / progress.current;
          const remainingGames = progress.total - progress.current;
          const newEstimate = Math.ceil(timePerGame * remainingGames);
          setEstimatedTime(newEstimate);
        }
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [startTime, loading, progress]);

  const handleAnalysis = async () => {
    if (!numGames) {
      toast.error('Please enter the number of games to analyze');
      return;
    }

    try {
      setLoading(true);
      setStartTime(Date.now());
      setProgress({ current: 0, total: parseInt(numGames) });
      // Initial estimate: 30 seconds per game
      setEstimatedTime(parseInt(numGames) * 30);

      const response = await fetch(`${API_BASE_URL}/games/batch-analyze/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${JSON.parse(localStorage.getItem('tokens')).access}`
        },
        body: JSON.stringify({ num_games: parseInt(numGames) })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to analyze games');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        try {
          const data = JSON.parse(chunk);
          if (data.progress) {
            setProgress(data.progress);
          }
        } catch (e) {
          console.error('Error parsing progress update:', e);
        }
      }

      const data = await response.json();
      setResults(data.results);
      toast.success('Batch analysis completed!');
    } catch (error) {
      console.error('Error during batch analysis:', error);
      toast.error(error.message || 'Failed to analyze games');
    } finally {
      setLoading(false);
      setStartTime(null);
      setEstimatedTime(0);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-3xl font-bold text-gray-900">Batch Analysis</h1>
          <p className="mt-2 text-sm text-gray-700">
            Analyze multiple games at once to get insights into your playing patterns.
          </p>
        </div>
      </div>

      <div className="mt-8 max-w-xl">
        <div className="space-y-6">
          <div>
            <label htmlFor="numGames" className="block text-sm font-medium text-gray-700">
              Number of Games to Analyze
            </label>
            <div className="mt-1">
              <input
                type="number"
                name="numGames"
                id="numGames"
                min="1"
                max="50"
                value={numGames}
                onChange={(e) => setNumGames(Math.min(50, Math.max(1, parseInt(e.target.value) || 1)))}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>
            <p className="mt-2 text-sm text-gray-500">Maximum 50 games can be analyzed at once.</p>
          </div>

          <button
            onClick={handleAnalysis}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
                Analyzing...
              </>
            ) : (
              'Start Analysis'
            )}
          </button>
        </div>

        {loading && (
          <div className="mt-4 space-y-4">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-sm text-gray-600">
              <span>Progress: {progress.current}/{progress.total} games</span>
              <span>Elapsed Time: {formatTime(elapsedTime)}</span>
              <span>Estimated Time Remaining: {formatTime(estimatedTime)}</span>
            </div>
          </div>
        )}

        {results && (
          <div className="mt-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Analysis Results</h2>
            
            {/* Overall Stats */}
            <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">Overall Statistics</h3>
              </div>
              <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Games Analyzed</dt>
                    <dd className="mt-1 text-sm text-gray-900">{results.overall_stats.total_games}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Average Accuracy</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {results.overall_stats.average_accuracy.toFixed(1)}%
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-gray-500">Results Distribution</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      Wins: {results.overall_stats.wins} | 
                      Draws: {results.overall_stats.draws} | 
                      Losses: {results.overall_stats.losses}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Improvement Areas */}
            {results.overall_stats.improvement_areas.length > 0 && (
              <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
                <div className="px-4 py-5 sm:px-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Areas for Improvement</h3>
                </div>
                <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                  <ul className="space-y-4">
                    {results.overall_stats.improvement_areas.map((area, index) => (
                      <li key={index} className="text-sm text-gray-900">
                        <span className="font-medium">{area.area}:</span> {area.description}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Strengths */}
            {results.overall_stats.strengths.length > 0 && (
              <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Your Strengths</h3>
                </div>
                <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                  <ul className="space-y-4">
                    {results.overall_stats.strengths.map((strength, index) => (
                      <li key={index} className="text-sm text-gray-900">
                        <span className="font-medium">{strength.area}:</span> {strength.description}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default BatchAnalysis;
