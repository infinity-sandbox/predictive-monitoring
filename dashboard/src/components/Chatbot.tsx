import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import '../styles/Chatbot.css';

const baseUrl = process.env.REACT_APP_BACKEND_API_URL;

interface Message {
  text: string;
  type: 'user' | 'bot';
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [initialMessageVisible, setInitialMessageVisible] = useState<boolean>(true);
  const accessToken = localStorage.getItem('accessToken');
  const refreshToken = localStorage.getItem('refreshToken');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const sendMessage = async () => {
    if (input.trim() === '') return;

    const userMessage: Message = { text: input, type: 'user' };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(baseUrl + '/api/v1/user/chatbot', 
        { question: input },
        {
          headers: {
            Authorization: accessToken ? `Bearer ${accessToken}` : '',
            'Refresh-Token': refreshToken || '',
            'Content-Type': 'application/json'
          }
        }
      );
      const botMessage: Message = { text: response.data.response, type: 'bot' };
      setLoading(false);
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      setLoading(false);
      const errorMessage: Message = { text: 'Error: Unable to get a response.', type: 'bot' };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
    if (initialMessageVisible) {
      setInitialMessageVisible(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {initialMessageVisible && (
          <div className="initial-message">
            Welcome to Applicare AI Chat!
          </div>
        )}
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="message bot loading">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-container">
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder="Talk to your data ... "
        />
        <button className="send-button" onClick={sendMessage} >
          Send
        </button>
      </div>
    </div>
  );
};

export default Chatbot;
