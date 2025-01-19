import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { toast } from "react-hot-toast";
import { Loader2 } from "lucide-react";

const API_BASE_URL = "http://localhost:8000/api";

const GameAnalysis = () => {
  const { gameId } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalysis();
  }, [gameId]);

  const fetchAnalysis = async () => {
    try {
      const accessToken = localStorage.getItem("tokens") ? JSON.parse(localStorage.getItem("tokens")).access : null;
      if (!accessToken) {
        toast.error("Please log in to view analysis");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/game/${gameId}/analysis/`, {
        headers: {
          "Authorization": `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to fetch analysis");
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error("Error fetching analysis:", error);
      setError(error.message);
      toast.error(error.message || "Failed to fetch analysis");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        <span className="ml-2">Loading analysis...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {error}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <p className="text-gray-500">No analysis available for this game.</p>
        </div>
      </div>
    );
  }

  const { feedback } = analysis;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Game Analysis</h1>

      {/* AI Feedback Section */}
      {feedback.ai_suggestions && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
          <div className="px-4 py-5 sm:px-6">
            <h2 className="text-lg font-medium text-gray-900">AI Analysis</h2>
            <p className="mt-1 text-sm text-gray-500">Personalized feedback from our AI assistant</p>
          </div>
          <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
            <div className="prose max-w-none">
              {typeof feedback.ai_suggestions === "string" ? (
                <p>{feedback.ai_suggestions}</p>
              ) : (
                Object.entries(feedback.ai_suggestions).map(([key, value]) => (
                  <div key={key} className="mb-4">
                    <h3 className="text-lg font-medium text-gray-900 capitalize">{key.replace(/_/g, " ")}</h3>
                    <p className="mt-2 text-gray-600">{value}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Game Statistics */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
        <div className="px-4 py-5 sm:px-6">
          <h2 className="text-lg font-medium text-gray-900">Game Statistics</h2>
        </div>
        <div className="border-t border-gray-200">
          <dl>
            <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Accuracy</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {feedback.accuracy ? `${feedback.accuracy.toFixed(1)}%` : "N/A"}
              </dd>
            </div>
            <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Mistakes</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                Blunders: {feedback.blunders || 0}, 
                Mistakes: {feedback.mistakes || 0}, 
                Inaccuracies: {feedback.inaccuracies || 0}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Opening Analysis */}
      {feedback.opening && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
          <div className="px-4 py-5 sm:px-6">
            <h2 className="text-lg font-medium text-gray-900">Opening Analysis</h2>
          </div>
          <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
            <div className="prose max-w-none">
              <p>{feedback.opening.evaluation}</p>
              {feedback.opening.suggestions && (
                <div className="mt-4">
                  <h3 className="text-md font-medium text-gray-900">Suggestions</h3>
                  <p>{feedback.opening.suggestions}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Middlegame Analysis */}
      {feedback.middlegame && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
          <div className="px-4 py-5 sm:px-6">
            <h2 className="text-lg font-medium text-gray-900">Middlegame Analysis</h2>
          </div>
          <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
            <div className="prose max-w-none">
              <p>{feedback.middlegame.evaluation}</p>
              {feedback.middlegame.suggestions && (
                <div className="mt-4">
                  <h3 className="text-md font-medium text-gray-900">Suggestions</h3>
                  <p>{feedback.middlegame.suggestions}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Endgame Analysis */}
      {feedback.endgame && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h2 className="text-lg font-medium text-gray-900">Endgame Analysis</h2>
          </div>
          <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
            <div className="prose max-w-none">
              <p>{feedback.endgame.evaluation}</p>
              {feedback.endgame.suggestions && (
                <div className="mt-4">
                  <h3 className="text-md font-medium text-gray-900">Suggestions</h3>
                  <p>{feedback.endgame.suggestions}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GameAnalysis;
