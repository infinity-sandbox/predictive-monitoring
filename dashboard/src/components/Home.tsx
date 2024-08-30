import React, { useState, useEffect } from 'react';
import '../styles/Home.css'; // Ensure the CSS file is correctly imported

interface HomeProps {
  message: string | null;
}

const Homepage: React.FC<HomeProps> = ({ message }) => {
  const [isCalculating, setIsCalculating] = useState(false);

  useEffect(() => {
    const intervalId = setInterval(() => {
      setIsCalculating(!isCalculating);
    }, 5000); // 5 seconds for demonstration; adjust as needed

    // Cleanup on component unmount
    return () => clearInterval(intervalId);
  }, [isCalculating]);

  return (
    <div className="homepage-container">
      <div className="circle"></div>
      <div className="message">
        {message || 'No problem detected'} {/* Show default message only if no message received */}
      </div>
    </div>
  );
};

export default Homepage;