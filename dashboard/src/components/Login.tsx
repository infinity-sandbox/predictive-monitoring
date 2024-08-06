// src/pages/Login.js
import React, { useState } from 'react';
import { Form, Input, Button, Alert, Spin, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import '../styles/Login.css';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const baseUrl = process.env.REACT_APP_BACKEND_API_URL;

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');          
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    const loginData = new URLSearchParams();
    loginData.append('username', values.email);
    loginData.append('password', values.password);

    setLoading(true);
    setError('');

    axios.post(baseUrl + "/api/v1/auth/login", loginData, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(_result => {
        const { token, access_token, refresh_token } = _result.data;
        localStorage.setItem('token', token);
        localStorage.setItem('accessToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);   
        message.success('Login successful');
        navigate('/home');
    })
    .catch(err => {
        message.error("Invalid credentials");
        console.error(err);
    })
    .finally(() => {
        setLoading(false);
    });
  }

  return (
    <div className='LoginPage'>
      <div className="login-container">
        <div>
          <Form
            name="login"
            onFinish={onFinish}
            className="login-form"
          >
            <h1 className='loginLeable'>Login</h1>
            {error && <Alert message={error} type="error" showIcon />}
            <div className='EmailText'>Email</div>
            <Form.Item className='emailInput'
              name="email"
              rules={[
                { required: true, message: 'Please input your email!' },
                { type: 'email', message: 'The input is not valid email!' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                className='emailInput'
                placeholder='Email'
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
            </Form.Item>
            <div className='PasswordText'>
              <div>Password</div>
              <div className="forgot-link">
                <Link to="/forgot/password">Forgot?</Link>
              </div>
            </div>
            <Form.Item className='passwordInput'
              name="password"
              rules={[
                { required: true, message: 'Please input your password!' },
                { min: 6, message: 'Password must be at least 6 characters!' },
              ]}
            >
              <Input
                prefix={<LockOutlined />}
                type="password"
                placeholder='Password'
                className='passwordInput'
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
            </Form.Item>
            <Form.Item>
              <Button htmlType="submit" className="login-button" disabled={loading}>
                {loading ? <Spin /> : 'Login Now'}
              </Button>
            </Form.Item>
            <div className="signup-link">
              <span>Don't have an account?</span>{" "}
              <Link to="/Register">Register</Link>
            </div>
          </Form>
        </div>
      </div>
      <div className="Right-side">
      </div>
    </div>
  );
};

export default Login;
