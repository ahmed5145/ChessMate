import React, { useState, useEffect } from "react";
import { analyzeBatchGames } from "../api";
import { useNavigate, useLocation } from "react-router-dom";
import { CheckCircle, AlertCircle, Clock, Info, Target, Loader, Activity, ChevronLeft } from "lucide-react";
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./BatchAnalysis.css";

const BatchAnalysis = () => {
  const [batchAnalysis, setBatchAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(0);
  const location = useLocation();
  const navigate = useNavigate();
  const numGames = location.state?.numGames || 50;

  useEffect(() => {
    const fetchBatchAnalysis = async () => {
      try {
        setProgress(0);
        const startTime = Date.now();
        const data = await analyzeBatchGames(numGames);
        const endTime = Date.now();
        const timeTaken = (endTime - startTime) / 1000; // in seconds
        setEstimatedTime(timeTaken);
        console.log("Batch analysis data:", data);
        setBatchAnalysis(data.results);
        setProgress(100);
      } catch (error) {
        console.error("Error performing batch analysis:", error);
        toast.error("An error occurred while performing batch analysis. Please try again.", {
          position: "top-right",
          autoClose: 5000,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchBatchAnalysis();
  }, [numGames]);

  useEffect(() => {
    if (loading && progress < 100) {
      const interval = setInterval(() => {
        setProgress((prevProgress) => {
          const increment = numGames > 20 ? 1 : 2; // Faster progress for fewer games
          const newProgress = Math.min(prevProgress + increment, 95); // Cap at 95% until complete
          return newProgress;
        });
      }, Math.max(100, estimatedTime * 10)); // Minimum interval of 100ms
      return () => clearInterval(interval);
    }
  }, [loading, estimatedTime, numGames, progress]);

  if (loading) {
    return (
      <div className="loading-screen">
        <Loader className="loader-icon animate-spin" />
        <h2 className="text-xl font-semibold mb-4">Analyzing {numGames} Games...</h2>
        <div className="progress-bar">
          <div className="progress" style={{ width: `${progress}%` }}></div>
        </div>
        <p className="mt-2 text-gray-600">{progress.toFixed(1)}% Complete</p>
        <p className="mt-1 text-sm text-gray-500">
          {progress < 100 
            ? "Analyzing moves and generating insights..."
            : "Finalizing analysis..."}
        </p>
        <p className="mt-1 text-sm text-gray-500">
          Estimated time remaining: {((estimatedTime * (100 - progress)) / 100).toFixed(1)} seconds
        </p>
      </div>
    );
  }

  if (!batchAnalysis) {
    return (
      <div className="loading-screen">
        <AlertCircle className="loader-icon" />
        <h2>Error loading analysis results. Please try again later.</h2>
      </div>
    );
  }

  return (
    <div className="batch-analysis-results">
      <h2 className="text-2xl font-bold mb-4 text-gray-800 flex items-center">
        <Activity className="w-6 h-6 mr-2" />
        Analysis Results
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="feedback-section bg-blue-50 p-4 rounded-lg">
          <h3 className="flex items-center text-blue-800">
            <Clock className="w-5 h-5 mr-2" />
            Time Management
          </h3>
          <div className="mt-3 text-gray-700">
            <p className="mb-2">
              <span className="font-medium">Average Time per Move:</span>{" "}
              {batchAnalysis.timeManagement?.avgTimePerMove?.toFixed(2) || "N/A"} seconds
            </p>
            <p className="text-sm bg-white p-3 rounded border border-blue-100">
              {batchAnalysis.timeManagement?.suggestion}
            </p>
          </div>
        </div>

        <div className="feedback-section bg-green-50 p-4 rounded-lg">
          <h3 className="flex items-center text-green-800">
            <Info className="w-5 h-5 mr-2" />
            Opening Analysis
          </h3>
          <div className="mt-3 text-gray-700">
            <p className="mb-2">
              <span className="font-medium">Common Openings:</span>{" "}
              {batchAnalysis.opening?.playedMoves?.join(", ") || "N/A"}
            </p>
            <p className="text-sm bg-white p-3 rounded border border-green-100">
              {batchAnalysis.opening?.suggestion}
            </p>
          </div>
        </div>

        <div className="feedback-section bg-purple-50 p-4 rounded-lg">
          <h3 className="flex items-center text-purple-800">
            <CheckCircle className="w-5 h-5 mr-2" />
            Endgame Performance
          </h3>
          <div className="mt-3 text-gray-700">
            <p className="mb-2">{batchAnalysis.endgame?.evaluation}</p>
            <p className="text-sm bg-white p-3 rounded border border-purple-100">
              {batchAnalysis.endgame?.suggestion}
            </p>
          </div>
        </div>

        <div className="feedback-section bg-yellow-50 p-4 rounded-lg">
          <h3 className="flex items-center text-yellow-800">
            <Target className="w-5 h-5 mr-2" />
            Tactical Opportunities
          </h3>
          <div className="mt-3 text-gray-700">
            {batchAnalysis.tacticalOpportunities?.length > 0 ? (
              <ul className="list-disc list-inside space-y-1">
                {batchAnalysis.tacticalOpportunities.map((opportunity, index) => (
                  <li key={index} className="text-sm">{opportunity}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm bg-white p-3 rounded border border-yellow-100">
                No significant tactical opportunities were missed in the analyzed games.
              </p>
            )}
          </div>
        </div>
      </div>

      {batchAnalysis.dynamicFeedback && (
        <div className="feedback-section mt-6 bg-indigo-50 p-4 rounded-lg">
          <h3 className="flex items-center text-indigo-800">
            <AlertCircle className="w-5 h-5 mr-2" />
            Overall Assessment
          </h3>
          <div className="mt-3 text-gray-700">
            <p className="text-sm bg-white p-3 rounded border border-indigo-100">
              {batchAnalysis.dynamicFeedback}
            </p>
          </div>
        </div>
      )}

      <div className="flex justify-center mt-8">
        <button
          onClick={() => navigate("/dashboard")}
          className="px-6 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center"
        >
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default BatchAnalysis;
