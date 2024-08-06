import React from 'react';
import { Routes, Route, BrowserRouter } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import ForgotPassword from '../src/components/forgetLink/forgetLinkPage'
import PasswordResetPage from '../src/components/forgetLink/emailRedirectedPage'
import SuccessRegistrationPage from '../src/components/statusPages/successRegistrationPage'
import PrivateRoute from './components/PrivateRoute';
import Register from './components/RegisterForm';
import './App.css';


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path='/dashboard' element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path='/forgot/password' element={<ForgotPassword />} />
        <Route path='/reset/password' element={<PasswordResetPage />} />
        <Route path='/success/registration' element={<SuccessRegistrationPage />} />
        <Route path='/register' element={<Register />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
