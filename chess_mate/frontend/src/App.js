import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import BatchAnalysis from './components/BatchAnalysis';
import SingleGameAnalysis from './components/SingleGameAnalysis';
import FetchGames from './components/FetchGames';
import Credits from './components/Credits';
import Navbar from './components/Navbar';
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <ToastContainer position="top-right" autoClose={5000} />
        <Navbar />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/batch-analysis"
            element={
              <PrivateRoute>
                <BatchAnalysis />
              </PrivateRoute>
            }
          />
          <Route
            path="/analysis/:gameId"
            element={
              <PrivateRoute>
                <SingleGameAnalysis />
              </PrivateRoute>
            }
          />
          <Route
            path="/fetch-games"
            element={
              <PrivateRoute>
                <FetchGames />
              </PrivateRoute>
            }
          />
          <Route
            path="/credits"
            element={
              <PrivateRoute>
                <Credits />
              </PrivateRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
