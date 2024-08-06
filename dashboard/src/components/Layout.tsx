// Layout.tsx
import React from 'react';
import Sidebar from './Sidebar';
import { Outlet } from 'react-router-dom'; // Used to render nested routes

const Layout: React.FC = () => {
  return (
    <div className="layout-container">
      <Sidebar />
      <div className="main-content">
        <Outlet /> {/* Renders the matched route's element */}
      </div>
    </div>
  );
};

export default Layout;
