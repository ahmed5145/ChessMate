import React, { useEffect, useState } from "react";
import { fetchGameFeedback } from "../api";
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Info,
  Play,
  Target,
  TrendingUp,
  Award,
  Loader
} from "lucide-react";
import "./GameFeedback.css";

const GameFeedback = ({ gameId }) => {
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFeedback = async () => {
      try {
        setLoading(true);
        const data = await fetchGameFeedback(gameId);
        setFeedback(data);
      } catch (err) {
        setError("Failed to fetch feedback. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchFeedback();
  }, [gameId]);

  if (loading) {
    return (
      <div className="loading-feedback flex items-center justify-center p-8">
        <Loader className="w-6 h-6 animate-spin text-blue-500 mr-3" />
        <span className="text-gray-600">Loading analysis...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="feedback-error bg-red-50 p-4 rounded-lg flex items-center text-red-800">
        <AlertCircle className="w-5 h-5 mr-2" />
        {error}
      </div>
    );
  }

  if (!feedback) {
    return (
      <div className="feedback-error bg-yellow-50 p-4 rounded-lg flex items-center text-yellow-800">
        <Info className="w-5 h-5 mr-2" />
        No feedback available for this game.
      </div>
    );
  }

  const sections = [
    {
      title: "Game Overview",
      icon: <Play className="w-5 h-5" />,
      color: "blue",
      content: (
        <div>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-white rounded-lg border border-blue-100">
              <p className="text-sm text-gray-500">Mistakes</p>
              <p className="text-xl font-semibold text-blue-600">{feedback.mistakes}</p>
            </div>
            <div className="text-center p-3 bg-white rounded-lg border border-blue-100">
              <p className="text-sm text-gray-500">Blunders</p>
              <p className="text-xl font-semibold text-red-600">{feedback.blunders}</p>
            </div>
            <div className="text-center p-3 bg-white rounded-lg border border-blue-100">
              <p className="text-sm text-gray-500">Inaccuracies</p>
              <p className="text-xl font-semibold text-yellow-600">{feedback.inaccuracies}</p>
            </div>
          </div>
          <p className="text-sm bg-white p-3 rounded border border-blue-100">
            {feedback.overview_suggestion || "Analysis of your game shows areas for improvement in accuracy and decision making."}
          </p>
        </div>
      ),
    },
    {
      title: "Time Management",
      icon: <Clock className="w-5 h-5" />,
      color: "green",
      content: (
        <div>
          <div className="mb-3">
            <p className="mb-2">
              <span className="font-medium">Average Time per Move:</span>{" "}
              {feedback.time_management.avg_time_per_move?.toFixed(2) || "N/A"} seconds
            </p>
            {feedback.time_management.critical_moments && (
              <p className="mb-2">
                <span className="font-medium">Critical Time Moments:</span>{" "}
                {feedback.time_management.critical_moments}
              </p>
            )}
          </div>
          <p className="text-sm bg-white p-3 rounded border border-green-100">
            {feedback.time_management.suggestion}
          </p>
        </div>
      ),
    },
    {
      title: "Opening Analysis",
      icon: <Info className="w-5 h-5" />,
      color: "purple",
      content: (
        <div>
          <p className="mb-2">
            <span className="font-medium">Opening Line:</span>{" "}
            {feedback.opening.played_moves.join(", ")}
          </p>
          <p className="text-sm bg-white p-3 rounded border border-purple-100">
            {feedback.opening.suggestion}
          </p>
        </div>
      ),
    },
    {
      title: "Endgame Performance",
      icon: <CheckCircle className="w-5 h-5" />,
      color: "indigo",
      content: (
        <div>
          <p className="mb-2">{feedback.endgame.evaluation}</p>
          <p className="text-sm bg-white p-3 rounded border border-indigo-100">
            {feedback.endgame.suggestion}
          </p>
        </div>
      ),
    },
    {
      title: "Tactical Opportunities",
      icon: <Target className="w-5 h-5" />,
      color: "yellow",
      content: (
        <div>
          {feedback.tactical_opportunities.length > 0 ? (
            <ul className="space-y-2">
              {feedback.tactical_opportunities.map((opportunity, index) => (
                <li key={index} className="text-sm bg-white p-3 rounded border border-yellow-100">
                  {opportunity}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm bg-white p-3 rounded border border-yellow-100">
              No significant tactical opportunities were missed in this game.
            </p>
          )}
        </div>
      ),
    },
    {
      title: "Improvement Areas",
      icon: <TrendingUp className="w-5 h-5" />,
      color: "red",
      content: (
        <div>
          {feedback.improvement_areas ? (
            <ul className="space-y-2">
              {feedback.improvement_areas.map((area, index) => (
                <li key={index} className="text-sm bg-white p-3 rounded border border-red-100">
                  {area}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm bg-white p-3 rounded border border-red-100">
              Keep practicing and analyzing your games to identify specific areas for improvement.
            </p>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="feedback-container max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6 text-gray-800 flex items-center">
        <Award className="w-6 h-6 mr-2" />
        Game Analysis
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sections.map((section, index) => (
          <div
            key={index}
            className={`feedback-section bg-${section.color}-50 p-4 rounded-lg`}
          >
            <h3 className={`flex items-center text-${section.color}-800 font-semibold mb-3`}>
              {React.cloneElement(section.icon, { className: "mr-2" })}
              {section.title}
            </h3>
            <div className="text-gray-700">
              {section.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GameFeedback;
