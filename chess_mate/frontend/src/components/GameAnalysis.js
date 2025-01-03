import React, { useState, useEffect } from "react";
import axios from "axios";
import { useParams } from "react-router-dom";

const GameAnalysis = () => {
  const { gameId } = useParams();
  const [analysis, setAnalysis] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await axios.get(`/api/game/${gameId}/analysis/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access")}`,
          },
        });
        setAnalysis(response.data.analysis);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching analysis:", error);
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [gameId]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Game Analysis</h1>
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
