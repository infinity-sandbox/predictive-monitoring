import React, { useState } from 'react';
import { Form, Input, Button, Checkbox, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined, QuestionCircleOutlined, HomeOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/RegisterForm.css';

const baseUrl = process.env.REACT_APP_BACKEND_API_URL;

const Register: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const onFinish = (values: any) => {
    setLoading(true);
    axios.post(baseUrl + '/api/v1/user/register', values)
      .then(_result => {
        message.success('Registration successful!');
        navigate('/success/registration');
      })
      .catch(err => {
        message.error('Registration failed. Please try again.');
        console.error(err);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div className='RegisterPageAll'>
      <div className="left-side"></div>
      <div className="register-container">
        <Form
          form={form}
          name="register"
          onFinish={onFinish}
          className="register-form"
        >
          <h1 className='createAccount'>Create an Account</h1>

          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Please enter your username.' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder='Username'
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[{ required: true, message: 'Please enter your email address.' }, { type: 'email', message: 'The input is not valid E-mail!' }]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder='Email Address'
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please enter your password.' }]}
          >
            <Input
              prefix={<LockOutlined />}
              type="password"
              placeholder='Password'
            />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            dependencies={['password']}
            hasFeedback
            rules={[
              { required: true, message: 'Please confirm your password.' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('The two passwords that you entered do not match!'));
                },
              }),
            ]}
          >
            <Input
              prefix={<LockOutlined />}
              type="password"
              placeholder='Confirm Password'
            />
          </Form.Item>

          <Form.Item
            name="phone_number"
            rules={[{ required: true, message: 'Please enter your phone number.' }]}
          >
            <Input
              prefix={<PhoneOutlined />}
              placeholder='Phone Number'
            />
          </Form.Item>

          <Form.Item
            name="address"
            rules={[{ required: true, message: 'Please enter your address.' }]}
          >
            <Input
              prefix={<HomeOutlined />}
              placeholder='Address'
            />
          </Form.Item>

          <Form.Item
            name="security_question"
            rules={[{ required: true, message: 'Please select a security question.' }]}
          >
            <Input
              prefix={<QuestionCircleOutlined />}
              placeholder='Security Question'
            />
          </Form.Item>

          <Form.Item
            name="security_answer"
            rules={[{ required: true, message: 'Please provide an answer to the security question.' }]}
          >
            <Input
              prefix={<QuestionCircleOutlined />}
              placeholder='Security Answer'
            />
          </Form.Item>
        <div className='bottoms'>
          <Form.Item
            name="agreeToTerms"
            valuePropName="checked"
            rules={[{ validator: (_, value) => value ? Promise.resolve() : Promise.reject(new Error('You must agree to the terms and conditions.')) }]}
          >
            <Checkbox>
              I agree to the terms and conditions
            </Checkbox>
          </Form.Item>

          <Form.Item>
            <Button htmlType="submit" className="register-button" loading={loading}>
              {loading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </Form.Item>
          <div className="login-link">
            Already have an account? <Link to="/login">Login</Link>
          </div>
        </div>
        </Form>
      </div>
    </div>
  );
};

export default Register;
