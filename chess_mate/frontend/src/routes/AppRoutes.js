import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from '../components/Login';
import Register from '../components/Register';
import ForgotPassword from '../components/ForgotPassword';
import ResetPassword from '../components/ResetPassword';
import ResetPasswordSuccess from '../components/ResetPasswordSuccess';
import ResetPasswordFailed from '../components/ResetPasswordFailed';
import UserProfile from '../components/UserProfile';
import Dashboard from '../components/Dashboard';
import BatchAnalysis from '../components/BatchAnalysis';
import FetchGames from '../components/FetchGames';
import Credits from '../components/Credits';
import PaymentSuccess from '../components/PaymentSuccess';
import PaymentCancel from '../components/PaymentCancel';
import Games from '../components/Games';
import PrivateRoute from '../components/PrivateRoute';
import GameAnalysis from '../components/GameAnalysis';
import ProtectedRoute from './ProtectedRoute';

const AppRoutes = () => {
  const isAuthenticated = !!localStorage.getItem('tokens');

  return (
    <Routes>
      <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />
      <Route path="/password-reset-success" element={<ResetPasswordSuccess />} />
      <Route path="/password-reset-failed" element={<ResetPasswordFailed />} />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <UserProfile />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analysis/:gameId"
        element={
          <ProtectedRoute>
            <GameAnalysis />
          </ProtectedRoute>
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
        path="/fetch-games"
        element={
          <PrivateRoute>
            <FetchGames />
          </PrivateRoute>
        }
      />
      <Route
        path="/games"
        element={
          <PrivateRoute>
            <Games />
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
      <Route
        path="/payment/success"
        element={
          <PrivateRoute>
            <PaymentSuccess />
          </PrivateRoute>
        }
      />
      <Route
        path="/payment/cancel"
        element={
          <PrivateRoute>
            <PaymentCancel />
          </PrivateRoute>
        }
      />
    </Routes>
  );
};

export default AppRoutes; 