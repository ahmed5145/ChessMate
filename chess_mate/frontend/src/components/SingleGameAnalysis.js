import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { analyzeSpecificGame } from '../api';
import {
  TrendingUp,
  Clock,
  Target,
  Award,
  Sword,
  Crown,
  AlertTriangle,
  Zap,
  BarChart2,
  Loader,
} from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import './SingleGameAnalysis.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const SingleGameAnalysis = () => {
  const { gameId } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        const data = await analyzeSpecificGame(gameId);
        if (!data || !data.analysis) {
          throw new Error('Invalid analysis data received');
        }
        setAnalysis(data);
      } catch (err) {
        setError('Failed to analyze game. Please try again.');
        console.error('Analysis error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [gameId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <Loader className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-700">Analyzing Game...</h2>
          <p className="text-gray-500 mt-2">This may take a few moments</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center text-red-600">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4" />
          <h2 className="text-xl font-semibold">{error}</h2>
        </div>
      </div>
    );
  }

  if (!analysis || !analysis.analysis || !Array.isArray(analysis.analysis)) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center text-gray-600">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4" />
          <h2 className="text-xl font-semibold">No analysis data available</h2>
        </div>
      </div>
    );
  }

  const chartData = {
    labels: analysis.analysis.map(move => `Move ${move.move_number}`),
    datasets: [
      {
        label: 'Position Evaluation',
        data: analysis.analysis.map(move => move.score / 100), // Convert centipawns to pawns
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Game Evaluation Over Time',
      },
      tooltip: {
        callbacks: {
          label: (context) => `Evaluation: ${context.raw.toFixed(2)} pawns`,
        },
      },
    },
    scales: {
      y: {
        title: {
          display: true,
          text: 'Evaluation (pawns)',
        },
      },
    },
  };

  const renderOverview = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <div className="bg-white p-6 rounded-xl shadow-sm">
        <div className="flex items-center mb-4">
          <Award className="w-6 h-6 text-blue-500 mr-2" />
          <h3 className="text-lg font-semibold">Game Statistics</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Accuracy</p>
            <p className="text-2xl font-bold text-blue-600">
              {((analysis.feedback?.accuracy || 0) * 100).toFixed(1)}%
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Mistakes</p>
            <p className="text-2xl font-bold text-yellow-600">
              {analysis.feedback?.mistakes || 0}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Blunders</p>
            <p className="text-2xl font-bold text-red-600">
              {analysis.feedback?.blunders || 0}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Avg Time/Move</p>
            <p className="text-2xl font-bold text-green-600">
              {analysis.feedback?.time_management?.avg_time_per_move?.toFixed(1) || 0}s
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm">
        <div className="flex items-center mb-4">
          <TrendingUp className="w-6 h-6 text-purple-500 mr-2" />
          <h3 className="text-lg font-semibold">Key Insights</h3>
        </div>
        <ul className="space-y-3">
          {analysis.feedback?.tactical_opportunities?.map((opportunity, index) => (
            <li key={index} className="flex items-start">
              <Zap className="w-5 h-5 text-yellow-500 mr-2 flex-shrink-0 mt-0.5" />
              <span className="text-gray-700">{opportunity}</span>
            </li>
          )) || (
            <li className="text-gray-500">No tactical opportunities identified.</li>
          )}
        </ul>
      </div>

      {renderTimeManagement()}
      {renderTacticalAnalysis()}
      {renderStatistics()}
    </div>
  );

  const renderMoveList = () => (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Move</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Evaluation</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {analysis.analysis.map((move, index) => (
              <tr key={index} className={move.is_critical ? 'bg-yellow-50' : ''}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-900">{move.move_number}.</span>
                    <span className="ml-2 text-sm text-gray-900">{move.move}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`text-sm ${move.score > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {(move.score / 100).toFixed(2)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {move.time_spent ? `${move.time_spent.toFixed(1)}s` : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {move.is_critical && <span className="text-yellow-600">Critical position</span>}
                  {move.is_check && <span className="text-red-600 ml-2">Check</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderTimeManagement = () => (
    <div className="bg-white p-6 rounded-xl shadow-sm">
      <div className="flex items-center mb-4">
        <Clock className="w-6 h-6 text-green-500 mr-2" />
        <h3 className="text-lg font-semibold">Time Management</h3>
      </div>
      <div className="space-y-4">
        <p className="text-gray-700">
          Average time per move: {analysis.feedback?.time_management?.avg_time_per_move?.toFixed(1) || 0}s
        </p>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-sm text-gray-600">
            {analysis.feedback?.time_management?.suggestion || 'Focus on managing your time effectively throughout the game.'}
          </p>
        </div>
      </div>
    </div>
  );

  const renderTacticalAnalysis = () => (
    <div className="bg-white p-6 rounded-xl shadow-sm">
      <div className="flex items-center mb-4">
        <Target className="w-6 h-6 text-purple-500 mr-2" />
        <h3 className="text-lg font-semibold">Tactical Analysis</h3>
      </div>
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Blunders</p>
            <p className="text-xl font-bold text-red-600">{analysis.feedback?.blunders || 0}</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Mistakes</p>
            <p className="text-xl font-bold text-yellow-600">{analysis.feedback?.mistakes || 0}</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Inaccuracies</p>
            <p className="text-xl font-bold text-orange-600">{analysis.feedback?.inaccuracies || 0}</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderStatistics = () => (
    <div className="bg-white p-6 rounded-xl shadow-sm">
      <div className="flex items-center mb-4">
        <BarChart2 className="w-6 h-6 text-blue-500 mr-2" />
        <h3 className="text-lg font-semibold">Statistics</h3>
      </div>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Critical Positions</p>
            <p className="text-xl font-bold text-indigo-600">
              {analysis.analysis.filter(move => move.is_critical).length}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Accuracy</p>
            <p className="text-xl font-bold text-green-600">
              {((analysis.feedback?.accuracy || 0) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Sword className="w-8 h-8 mr-3 text-blue-500" />
          Game Analysis
        </h1>
        <p className="mt-2 text-gray-600">
          Analyzed on {new Date(analysis.game_info?.played_at).toLocaleDateString()}
        </p>
      </div>

      <div className="mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>

      <div className="mb-6">
        <nav className="flex space-x-4">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'overview'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('moves')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'moves'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Move List
          </button>
        </nav>
      </div>

      {activeTab === 'overview' ? renderOverview() : renderMoveList()}

      <div className="mt-8 bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center mb-4">
          <Crown className="w-6 h-6 text-yellow-500 mr-2" />
          <h3 className="text-lg font-semibold">Improvement Suggestions</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-800 mb-2">Opening</h4>
              <p className="text-blue-900">{analysis.feedback?.opening?.suggestion || 'No opening suggestions available.'}</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <h4 className="font-medium text-green-800 mb-2">Time Management</h4>
              <p className="text-green-900">{analysis.feedback?.time_management?.suggestion || 'No time management suggestions available.'}</p>
            </div>
          </div>
          <div className="space-y-4">
            <div className="p-4 bg-purple-50 rounded-lg">
              <h4 className="font-medium text-purple-800 mb-2">Tactics</h4>
              <p className="text-purple-900">
                {analysis.feedback?.tactical_opportunities?.length > 0
                  ? "Review the tactical opportunities you missed during the game."
                  : "Good tactical awareness in this game."}
              </p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-medium text-yellow-800 mb-2">Endgame</h4>
              <p className="text-yellow-900">{analysis.feedback?.endgame?.suggestion || 'No endgame suggestions available.'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SingleGameAnalysis; 