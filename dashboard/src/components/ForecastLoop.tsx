import React, { useEffect } from 'react';

interface ForecastLoopProps {
  setMessage: (message: string) => void;
}

const websocketUrl = process.env.REACT_APP_WEBSOCKET_URL;

const ForecastLoop: React.FC<ForecastLoopProps> = ({ setMessage }) => {
  useEffect(() => {
    const authorization = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');

    console.log('Authorization Token:', authorization);
    console.log('Refresh Token:', refreshToken);

    if (!authorization || !refreshToken) {
      console.error("Authorization or refresh token not found");
      return;
    }

    const socket = new WebSocket(`${websocketUrl}/api/v1/varmax/forecast/loop`);

    socket.onopen = () => {
      console.log('WebSocket connection established');
      socket.send(JSON.stringify({
        authorization,
        refresh_token: refreshToken,
      }));
    };

    socket.onmessage = (event) => {
      console.log('Received:', event.data);
      setMessage(event.data); // Pass the WebSocket message to the parent
    };

    socket.onclose = () => {
      console.log('WebSocket connection closed');
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      socket.close();
    };
  }, [setMessage]);

  return null;
};

export default ForecastLoop;