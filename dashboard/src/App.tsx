import React from 'react';
import { Routes, Route, BrowserRouter } from 'react-router-dom';
import Login from './components/Login';
import ForgotPassword from './components/forgetLink/forgetLinkPage'
import PasswordResetPage from './components/forgetLink/emailRedirectedPage'
import SuccessRegistrationPage from './components/statusPages/successRegistrationPage'
import PrivateRoute from './components/PrivateRoute';
import Register from './components/RegisterForm';
import Layout from './components/Layout';
import Home from './components/Home';
import Chatbot from './components/Chatbot';
import Dashboard from './components/Dashboard';
import './App.css';


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path='/forgot/password' element={<ForgotPassword />} />
        <Route path='/reset/password' element={<PasswordResetPage />} />
        <Route path='/success/registration' element={<SuccessRegistrationPage />} />
        <Route path='/register' element={<Register />} />
        <Route element={<Layout />}> {/* Wrap routes with Layout */}
        {/* TODO: ALWASY ADD TOKEN IN HERE /home?token=...... or :TODO: INISE ROUTE*/}
          <Route path="/home" element={<PrivateRoute><Home /></PrivateRoute>} />
          <Route path="/chatbot" element={<PrivateRoute><Chatbot /></PrivateRoute>} />
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
