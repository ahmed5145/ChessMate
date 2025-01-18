import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { fetchGameAnalysis, analyzeBatchGames } from "../api"; // Import the new API function

const GameAnalysis = () => {
  const { gameId } = useParams();
  const [analysis, setAnalysis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [batchAnalysis, setBatchAnalysis] = useState(null); // State for batch analysis results
  const [numGames, setNumGames] = useState(50); // State for number of games to analyze

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const data = await fetchGameAnalysis(`api/game/${gameId}/analysis/`);
        setAnalysis(data.analysis);
      } catch (error) {
        console.error("Error fetching analysis:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [gameId]);

  const handleBatchAnalysis = async () => {
    try {
      const data = await analyzeBatchGames(numGames);
      setBatchAnalysis(data.results);
    } catch (error) {
      console.error("Error performing batch analysis:", error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Game Analysis</h1>
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Number of Games to Analyze:
        </label>
        <input
          type="number"
          value={numGames}
          onChange={(e) => setNumGames(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>
      <button
        onClick={handleBatchAnalysis}
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
      >
        Analyze All Games
      </button>
      {batchAnalysis && (
        <div className="batch-analysis-results">
          <h2 className="text-xl font-bold mb-2">Batch Analysis Results</h2>
          <ul className="list-disc ml-5">
            {Object.entries(batchAnalysis).map(([gameId, analysis], index) => (
              <li key={index}>
                <strong>Game ID:</strong> {gameId}
                <ul>
                  {analysis.map((move, idx) => (
                    <li key={idx}>
                      <strong>Move:</strong> {move.move}, <strong>Score:</strong> {move.score}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      )}
      {loading ? (
        <p>Loading analysis...</p>
      ) : analysis.length > 0 ? (
        <ul className="list-disc ml-5">
          {analysis.map((move, index) => (
            <li key={index}>
              <strong>Move:</strong> {move.move}, <strong>Score:</strong> {move.score}
            </li>
          ))}
        </ul>
      ) : (
        <p>No analysis data available.</p>
      )}
    </div>
  );
};

export default GameAnalysis;
