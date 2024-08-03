import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button, Select, Spin, Row, Col, Divider } from 'antd';
import { Line, Bar } from 'react-chartjs-2';
import 'chart.js/auto'; // Import the necessary chart.js components
import '../styles/Dashboard.css';

const { Option } = Select;
const baseUrl = process.env.REACT_APP_BACKEND_API_URL;

interface DropdownItem {
  value: string;
  label: string;
}

interface DataWithDate {
  date: string[];
  [key: string]: string[] | number[];
}

interface ForecastResponse {
  predictions: DataWithDate[];
  causes: { features: string[]; importance: number[] };
  train: DataWithDate[];
  test: DataWithDate[];
}

const Dashboard: React.FC = () => {
  const [days, setDays] = useState<number | undefined>(undefined);
  const [column, setColumn] = useState<string | undefined>(undefined);
  const [dropdownItems, setDropdownItems] = useState<DropdownItem[]>([]);
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    axios.get(baseUrl + '/api/v1/varmax/dropdown_data')
      .then(response => setDropdownItems(response.data))
      .catch(error => console.error('Error fetching dropdown data:', error));
  }, []);

  const handleForecast = () => {
    if (days !== undefined && column) {
      setLoading(true);
      axios.post(baseUrl + '/api/v1/varmax/forecaster', { days, column })
        .then(response => {
          setForecastData(response.data);
          setLoading(false);
        })
        .catch(error => {
          console.error('Error fetching forecast data:', error);
          setLoading(false);
        });
    }
  };

// NOTE: uncomment this block if you want d/t shades of color
// const colors: { [key: string]: string } = {
//     predictions: '#ff5733', // Orange
//     train: '#33ff57',      // Green
//     test: '#3357ff'        // Blue
//   };

const colors: { [key: string]: string } = {
    predictions: '#318CE7', // Blue
    train: '#318CE7',      // Green
    test: '#318CE7'        // Orange
  };
  
  const renderLineChart = (dataList: DataWithDate[], type: string) => {
    // Extract dates from the first entry
    const labels = dataList[0]?.date || [];
  
    // Create datasets for each column in the dataList
    const datasets = dataList.flatMap((data, index) => {
      // Determine the dataset type based on the index
      const datasetType = index === 0 ? 'predictions' : index === 1 ? 'train' : 'test';
      return Object.keys(data)
        .filter(key => key !== 'date') // Exclude the 'date' key
        .map((colName) => ({
          label: `${colName} (${datasetType.charAt(0).toUpperCase() + datasetType.slice(1)})`,
          data: data[colName] as number[], // Cast to number array
          borderColor: colors[datasetType] || '#318CE7', // Use color based on dataset type, default to blue
          backgroundColor: 'rgba(0,0,0,0)',
          borderWidth: 2,
          columnName: colName // Assign column name to the dataset for later use
        }));
    });
  
    // Collect unique column names manually
    const columnNames: string[] = [];
    datasets.forEach(dataset => {
      if (!columnNames.includes(dataset.columnName)) {
        columnNames.push(dataset.columnName);
      }
    });
    
    return (
      <Line
        data={{
          labels,
          datasets,
        }}
        options={{
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: `Forecast for ${columnNames.join(', ')}`, // Use column names for the title
              font: {
                size: 16,
                weight: 'bold',
              },
              padding: {
                top: 10,
                bottom: 20,
              }
            }
          },
          scales: {
            x: { 
              beginAtZero: false,
              title: { 
                display: true, 
                text: 'Date'
              }
            },
            y: { 
              beginAtZero: false,
              title: { 
                display: true, 
                text: 'Value'
              }
            },
          },
        }}
      />
    );
  };
  
  const renderBarChart = (causes: { features: string[]; importance: number[] }, columnName: string) => {
    return (
      <Bar
        data={{
          labels: causes.features,
          datasets: [{
            label: 'Causes',
            data: causes.importance,
            backgroundColor: '#318CE7',
          }],
        }}
        options={{
          responsive: true,
          indexAxis: 'y', // This makes the chart horizontal
          plugins: {
            title: {
              display: true,
              text: `Causes for ${columnName}`, // Dynamic title
              padding: {
                top: 5,
                bottom: 10,
              },
              font: {
                size: 15,
                weight: 'bold',
              },
            },
          },
          scales: {
            x: { 
              beginAtZero: true,
              title: { 
                display: true, 
                text: 'Importance' 
              }
            },
            y: {
              title: { 
                display: true, 
                text: 'Features' 
              }
            },
          },
        }}
      />
    );
  };

  // Create array of numbers from 1 to 14
  const daysOptions = Array.from({ length: 14 }, (_, i) => i + 1);

  return (
    <div className="dashboard">
      <div className="selectors">
        <Select
          value={days}
          onChange={(value) => setDays(value)}
          style={{ width: 120, marginRight: 16, color: 'blue' }}
          placeholder="Days"
        >
          {daysOptions.map(day => (
            <Option key={day} value={day}>{day}</Option>
          ))}
        </Select>
        <Select
          value={column}
          onChange={(value) => setColumn(value)}
          style={{ width: 200, marginRight: 16, color: 'blue' }}
          placeholder="Select Column"
        >
          {dropdownItems.map(item => (
            <Option key={item.value} value={item.value}>{item.label}</Option>
          ))}
        </Select>
        <Button
          type="primary"
          onClick={handleForecast}
          disabled={days === undefined || column === undefined}
        >
          Forecast
        </Button>
      </div>

      {loading ? (
        <div className="loading">
          <Spin size="large" />
        </div>
      ) : (
        forecastData && (
          <>
            <Row gutter={16} className="charts-container">
              <Col span={16} className="main-chart">
                {renderLineChart([forecastData.predictions.slice(-1)[0], forecastData.train.slice(-1)[0], forecastData.test.slice(-1)[0]], 'Latest Data')}
              </Col>
              <Col span={8} className="side-chart">
                {renderBarChart(forecastData.causes, column || "N/A")} {/* Pass column name here */}
              </Col>
            </Row>
            <Divider />
            <h3><i>Forecasting Causes</i></h3>
            <Divider />
            <Row gutter={16} className="charts-container">
              {forecastData.predictions.slice(0, 3).map((_, index) => (
                <Col span={24} key={index} className="line-chart">
                  {renderLineChart(
                    [
                      forecastData.predictions[index],
                      forecastData.train[index],
                      forecastData.test[index]
                    ],
                    `Data Point ${index + 1}`
                  )}
                </Col>
              ))}
            </Row>
          </>
        )
      )}
    </div>
  );
};

export default Dashboard;

