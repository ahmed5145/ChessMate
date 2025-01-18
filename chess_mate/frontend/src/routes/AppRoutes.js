import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from '../components/Login';
import Register from '../components/Register';
import Dashboard from '../components/Dashboard';
import BatchAnalysis from '../components/BatchAnalysis';
import SingleGameAnalysis from '../components/SingleGameAnalysis';
import FetchGames from '../components/FetchGames';
import Credits from '../components/Credits';
import PaymentSuccess from '../components/PaymentSuccess';
import PaymentCancel from '../components/PaymentCancel';
import Games from '../components/Games';
import PrivateRoute from '../components/PrivateRoute';

const AppRoutes = () => {
  return (
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
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default AppRoutes; 