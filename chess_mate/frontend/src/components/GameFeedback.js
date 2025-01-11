import React, { useEffect, useState } from "react";
import { fetchGameFeedback } from "../api";
import { AlertCircle, CheckCircle, Clock, Info, Play, Target } from "lucide-react";
import "./GameFeedback.css";

const GameFeedback = ({ gameId }) => {
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);

  const sectionsPerPage = 3;

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

  const handleNextPage = () => {
    setCurrentPage((prevPage) => prevPage + 1);
  };

  const handlePrevPage = () => {
    setCurrentPage((prevPage) => prevPage - 1);
  };

  if (error) {
    return <div className="feedback-error"><AlertCircle /> {error}</div>;
  }

  if (!feedback) {
    return <div className="loading-feedback"><Clock /> Loading feedback...</div>;
  }

  const sections = [
    {
      title: "Overview",
      icon: <Play />,
      content: (
        <>
          <p>Mistakes: {feedback.mistakes}</p>
          <p>Blunders: {feedback.blunders}</p>
          <p>Inaccuracies: {feedback.inaccuracies}</p>
        </>
      ),
    },
    {
      title: "Time Management",
      icon: <Clock />,
      content: (
        <>
          <p>Average Time per Move: {feedback.time_management.avg_time_per_move || "N/A"} seconds</p>
          <p>Suggestion: {feedback.time_management.suggestion}</p>
        </>
      ),
    },
    {
      title: "Opening",
      icon: <Info />,
      content: (
        <>
          <p>Played Moves: {feedback.opening.played_moves.join(", ")}</p>
          <p>Suggestion: {feedback.opening.suggestion}</p>
        </>
      ),
    },
    {
      title: "Endgame",
      icon: <CheckCircle />,
      content: (
        <>
          <p>{feedback.endgame.evaluation}</p>
          <p>Suggestion: {feedback.endgame.suggestion}</p>
        </>
      ),
    },
    {
      title: "Tactical Opportunities",
      icon: <Target />,
      content: (
        <>
          {feedback.tactical_opportunities.length > 0 ? (
            <ul>
              {feedback.tactical_opportunities.map((opportunity, index) => (
                <li key={index}>{opportunity}</li>
              ))}
            </ul>
          ) : (
            <p>No tactical opportunities detected.</p>
          )}
        </>
      ),
    },
  ];

  const startIndex = (currentPage - 1) * sectionsPerPage;
  const endIndex = startIndex + sectionsPerPage;
  const currentSections = sections.slice(startIndex, endIndex);

  return (
    <div className="feedback-container">
      <h2><Target /> Game Feedback</h2>
      {currentSections.map((section, index) => (
        <div className="feedback-section" key={index}>
          <h3>{section.icon} {section.title}</h3>
          {section.content}
        </div>
      ))}
      <div className="pagination-controls">
        <button onClick={handlePrevPage} disabled={currentPage === 1}>
          Previous
        </button>
        <button onClick={handleNextPage} disabled={endIndex >= sections.length}>
          Next
        </button>
      </div>
    </div>
  );
};

export default GameFeedback;
