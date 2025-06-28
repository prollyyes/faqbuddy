import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const Chart = ({ data }) => {
  const chartData = {
    labels: data.map((item) => item.corso),
    datasets: [
      {
        label: "Voto",
        data: data.map((item) => item.voto),
        backgroundColor: "#822433",
        barThickness: 15,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        min: 18,
        max: 30,
        ticks: {
          font: {
            weight: 'bold',
          },
          callback: function (value) {
            if (value >= 18 && value <= 30 && value % 2 === 0) return value;
            return '';
          },
        },
        title: {
          display: false,
          text: "Voto",
        },
      },
      x: {
        ticks: {
          font: {
            weight: 'bold',
          },
          autoSkip: false,
          maxRotation: 90,
          minRotation: 90,
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            return `Voto: ${context.raw}`;
          },
        },
      },
    },
  };

  return (
    <div style={{ width: '100%', maxWidth: '100%' }}>
      <div style={{ width: '100%', height: '260px' }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
};

export default Chart;