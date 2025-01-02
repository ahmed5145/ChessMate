import './App.css';
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import GameAnalysis from "./components/GameAnalysis";

function App() {
  return (
    <Router>
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/analysis/:gameId" element={<GameAnalysis />} />
    </Routes>
  </Router>
  );
}

export default App;
