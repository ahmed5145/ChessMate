import React, { useEffect, useState } from "react";
import { fetchGameFeedback } from "../api";
import { AlertCircle, CheckCircle, Clock, Info, Play, Target } from "lucide-react";
import "./GameFeedback.css";

const GameFeedback = ({ gameId }) => {
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFeedback = async () => {
      try {
        const data = await fetchGameFeedback(gameId);
        setFeedback(data);
      } catch (err) {
        setError("Failed to fetch feedback. Please try again.");
      }
    };

    fetchFeedback();
  }, [gameId]);

  if (error) {
    return <div className="feedback-error"><AlertCircle /> {error}</div>;
  }

  if (!feedback) {
    return <div className="loading-feedback"><Clock /> Loading feedback...</div>;
  }

  return (
    <div className="feedback-container">
      <h2><Target /> Game Feedback</h2>
      <div className="feedback-section">
        <h3><Play /> Overview</h3>
        <p>Mistakes: {feedback.mistakes}</p>
        <p>Blunders: {feedback.blunders}</p>
        <p>Inaccuracies: {feedback.inaccuracies}</p>
      </div>
      <div className="feedback-section">
        <h3><Clock /> Time Management</h3>
        <p>Average Time per Move: {feedback.time_management.avg_time_per_move || "N/A"} seconds</p>
        <p>Suggestion: {feedback.time_management.suggestion}</p>
      </div>
      <div className="feedback-section">
        <h3><Info /> Opening</h3>
        <p>Played Moves: {feedback.opening.played_moves.join(", ")}</p>
        <p>Suggestion: {feedback.opening.suggestion}</p>
      </div>
      <div className="feedback-section">
        <h3><CheckCircle /> Endgame</h3>
        <p>{feedback.endgame.evaluation}</p>
        <p>Suggestion: {feedback.endgame.suggestion}</p>
      </div>
      <div className="feedback-section">
        <h3><Target /> Tactical Opportunities</h3>
        {feedback.tactical_opportunities.length > 0 ? (
          <ul>
            {feedback.tactical_opportunities.map((opportunity, index) => (
              <li key={index}>{opportunity}</li>
            ))}
          </ul>
        ) : (
          <p>No tactical opportunities detected.</p>
        )}
      </div>
    </div>
  );
};

export default GameFeedback;
