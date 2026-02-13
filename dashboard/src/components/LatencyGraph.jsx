/**
 * SmartV2X-CP Ultra — Latency Graph
 * Real-time latency chart using Chart.js.
 */
import React, { useRef, useEffect } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler);

const MAX_POINTS = 40;

export default function LatencyGraph({ latencyData = [] }) {
    const labels = latencyData.slice(-MAX_POINTS).map((_, i) => `${i}`);
    const values = latencyData.slice(-MAX_POINTS);

    const data = {
        labels,
        datasets: [
            {
                label: 'Latency (ms)',
                data: values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                borderWidth: 2,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(17, 24, 39, 0.9)',
                titleColor: '#f1f5f9',
                bodyColor: '#94a3b8',
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1,
                cornerRadius: 8,
            },
        },
        scales: {
            x: {
                display: false,
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(255, 255, 255, 0.04)',
                },
                ticks: {
                    color: '#64748b',
                    font: { size: 11 },
                    callback: (v) => `${v}ms`,
                },
            },
        },
        animation: {
            duration: 300,
        },
    };

    return (
        <div className="chart-container">
            {values.length > 0 ? (
                <Line data={data} options={options} />
            ) : (
                <div className="empty-state">
                    <div className="icon">📊</div>
                    <p>Awaiting latency data</p>
                </div>
            )}
        </div>
    );
}
