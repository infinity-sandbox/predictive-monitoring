import React from 'react';
import { Navigate } from 'react-router-dom';
// {/* TODO: ALWASY ADD TOKEN IN HERE /home?token=...... */}
const PrivateRoute: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const isAuthenticated = !!localStorage.getItem('token'); // Check if token exists in local storage
  return isAuthenticated ? children : <Navigate to="/login" />;
};

export default PrivateRoute;