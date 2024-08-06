import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../images/arcturus.png'; // Adjust the path to your logo image

const Sidebar: React.FC = () => {
  return (
    <div className="sidebar">
      <img src={logo} alt="Logo" className="sidebar-icon" />
      <div className="nav-links">
        <Link to="/home" className="nav-link">Home</Link>
        <Link to="/chatbot" className="nav-link">Chatbot</Link>
        <Link to="/dashboard" className="nav-link">Dashboard</Link>
      </div>
    </div>
  );
}

export default Sidebar;
