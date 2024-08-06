import React, { useState, useEffect } from 'react';
import '../styles/Home.css'; // Ensure the CSS file is correctly imported

const Homepage: React.FC = () => {
  const [message, setMessage] = useState('No problem detected');
  const [isCalculating, setIsCalculating] = useState(false);

  useEffect(() => {
    const intervalId = setInterval(() => {
      if (isCalculating) {
        setMessage('No problem detected');
        setIsCalculating(false);
      } else {
        setMessage('Calculating problem ... ');
        setIsCalculating(true);
      }
    }, 5000); // 5 minutes in milliseconds

    // Cleanup on component unmount
    return () => clearInterval(intervalId);
  }, [isCalculating]);

  return (
    <div className="homepage-container">
      <div className="circle"></div>
      <div className="message">{message}</div>
    </div>
  );
};

export default Homepage;
