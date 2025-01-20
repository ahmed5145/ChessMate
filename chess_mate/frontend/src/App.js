import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Navbar';
import AppRoutes from './routes/AppRoutes';
import { UserProvider } from './contexts/UserContext';

function App() {
  return (
    <UserProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <AppRoutes />
          <Toaster position="top-right" />
        </div>
      </Router>
    </UserProvider>
  );
}

export default App;
