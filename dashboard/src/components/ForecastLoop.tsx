import React, { useEffect } from 'react';

const ForecastLoop: React.FC = () => {
    useEffect(() => {
        const authorization = localStorage.getItem('accessToken');
        const refreshToken = localStorage.getItem('refreshToken');
      
        console.log('Authorization Token:', authorization);
        console.log('Refresh Token:', refreshToken);
      
        if (!authorization || !refreshToken) {
          console.error("Authorization or refresh token not found");
          return;
        }
      
        const socket = new WebSocket(`ws://0.0.0.0:8000/api/v1/varmax/forecast/loop`);
      
        socket.onopen = () => {
          console.log('WebSocket connection established');
          socket.send(JSON.stringify({
            authorization,
            refresh_token: refreshToken,
          }));
        };
      
        socket.onmessage = (event) => {
          console.log('Received:', event.data);
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
    }, []);

  return null;
};

export default ForecastLoop;