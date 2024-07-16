import React, { useEffect } from 'react';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css'; // Import the CSS file

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Adding specific class names to the body and html elements
    document.body.classList.add('landing-body');
    document.documentElement.classList.add('landing-html');

    return () => {
      // Clean up the class names when the component is unmounted
      document.body.classList.remove('landing-body');
      document.documentElement.classList.remove('landing-html');
    };
  }, []);

  const enterDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <div className="landing-container">
      <div className="landing-content">
        <header className="landing-header">Applicare OS Monitor AI Pipeline</header>
        <Button className="landing-button" type="primary" size="large" onClick={enterDashboard}>
            Enter Dashboard
        </Button>
      </div>
    </div>
  );
};

export default LandingPage;
