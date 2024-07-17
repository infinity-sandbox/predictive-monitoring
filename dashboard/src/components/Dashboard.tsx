import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Typography, Spin, Button, Card, DatePicker, message } from 'antd';
import { Bar } from '@ant-design/charts';
import moment from 'moment';
import './Dashboard.css'; // Import the CSS file

const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [mlMetric, setMlMetric] = useState<number | null>(null);
  const [featureImportances, setFeatureImportances] = useState<{
    features: string[];
    importance: number[];
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [predictionDate, setPredictionDate] = useState<moment.Moment | null>(null);
  const [predictionResult, setPredictionResult] = useState<string | null>(null);
  const [predicting, setPredicting] = useState<boolean>(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('http://0.0.0.0:8000/api/v1/fetch_data/importance'); // Adjust URL as per your API endpoint
        setMlMetric(response.data.ml_metric);
        setFeatureImportances(response.data.casual_features);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        message.error('Error fetching data.');
      }
    };

    fetchData();
  }, []);

  const handlePredict = async () => {
    if (!predictionDate) {
      message.error('Please select a prediction date.');
      return;
    }

    setPredicting(true);

    try {
      const formattedDate = predictionDate.format('YYYY-MM-DD HH:mm');
      const response = await axios.post('http://0.0.0.0:8000/api/v1/fetch_data/predict', { date: formattedDate });
      setPredictionResult(response.data.prediction);
      message.success('Prediction successful!');
    } catch (error) {
      console.error('Error making prediction:', error);
      message.error('Error making prediction.');
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-cards">
        <Card className="dashboard-card">
          <Spin spinning={loading}>
            <Title level={4}>AI Model Error Threshold (MSE)</Title>
            <p>{mlMetric !== null ? mlMetric.toFixed(10) : 'Loading...'}</p>
          </Spin>
        </Card>
        <Card className="dashboard-card wide-card">
          <Spin spinning={loading}>
            <Title level={4}>Causes for CPU Performance Overload</Title>
            {featureImportances ? (
              <Bar
                data={featureImportances.importance.map((value, index) => ({
                  feature: featureImportances.features[index],
                  importance: value,
                }))}
                xField="feature"
                yField="importance"
                color="rgba(75, 192, 192, 0.6)"
                xAxis={{ label: { autoRotate: false } }}
                yAxis={{ label: { formatter: (v: any) => `${v}%` } }}
                meta={{
                  feature: { alias: 'Feature' },
                  importance: { alias: 'Importance' },
                }}
                height={400}
              />
            ) : (
              <p>Loading...</p>
            )}
          </Spin>
        </Card>
      </div>
      <div className="prediction-section">
        <Card className="prediction-card">
          <Title level={4}>Enter Prediction Date</Title>
          <DatePicker
            showTime
            format="YYYY-MM-DD HH:mm"
            value={predictionDate}
            onChange={(date) => setPredictionDate(date)}
            style={{ marginBottom: '10px', width: '100%' }}
          />
          <Button type="primary" onClick={handlePredict} loading={predicting} style={{ width: '100%' }}>
            Predict
          </Button>
        </Card>
        {predictionResult !== null && (
          <Card className="prediction-result-card">
            <Title level={4}>Prediction Result</Title>
            <p>{predictionResult}</p>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
