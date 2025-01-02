import React, { useState, useEffect } from "react";

const GameAnalysis = ({ gameId }) => {
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/game/${gameId}/analysis/`)
      .then((res) => res.json())
      .then((data) => setAnalysis(data.analysis))
      .catch((error) => console.error("Error fetching analysis:", error));
  }, [gameId]);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-800">Game Analysis</h1>
      {analysis ? (
        <ul className="mt-4">
          {analysis.map((move, index) => (
            <li key={index} className="py-2 border-b">
              Move {index + 1}: {move.move}, Score: {move.score}
            </li>
          ))}
        </ul>
      ) : (
        <p>Loading analysis...</p>
      )}
    </div>
  );
};

export default GameAnalysis;
