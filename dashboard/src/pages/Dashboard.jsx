/**
 * SmartV2X-CP Ultra — Dashboard Page
 * Main dashboard view assembling all components with WebSocket live data.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { V2XWebSocket } from '../api/websocket';
import { authHeaders } from '../api/auth';
import VehicleMap from '../components/VehicleMap';
import AlertPanel from '../components/AlertPanel';
import LatencyGraph from '../components/LatencyGraph';
import HealthPanel from '../components/HealthPanel';
import PairingStatus from '../components/PairingStatus';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Dashboard() {
    const { user, logout } = useAuth();
    const [vehicles, setVehicles] = useState({});
    const [alerts, setAlerts] = useState([]);
    const [latencyData, setLatencyData] = useState([]);
    const [health, setHealth] = useState({});
    const [wsConnected, setWsConnected] = useState(false);
    const wsRef = useRef(null);

    // WebSocket message handler
    const handleWSMessage = useCallback((msg) => {
        if (msg.type === 'vehicle_update') {
            setVehicles((prev) => ({
                ...prev,
                [msg.vehicle_id]: { vehicle_id: msg.vehicle_id, ...msg.data },
            }));

            // Track latency
            if (msg.timestamp) {
                const latency = (Date.now() / 1000 - msg.timestamp) * 1000;
                setLatencyData((prev) => [...prev.slice(-59), Math.max(0, latency)]);
            }

            // Track alerts for HIGH/MEDIUM risk
            const level = msg.data?.risk?.level;
            if (level === 'HIGH' || level === 'MEDIUM') {
                setAlerts((prev) => [
                    { vehicle_id: msg.vehicle_id, risk: msg.data.risk, timestamp: msg.timestamp },
                    ...prev.slice(0, 49),
                ]);
            }
        }

        if (msg.type === 'alert') {
            setAlerts((prev) => [msg.data, ...prev.slice(0, 49)]);
        }
    }, []);

    // Connect WebSocket
    useEffect(() => {
        wsRef.current = new V2XWebSocket(handleWSMessage, setWsConnected);
        wsRef.current.connect();

        return () => {
            if (wsRef.current) wsRef.current.disconnect();
        };
    }, [handleWSMessage]);

    // Poll health endpoint
    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const resp = await fetch(`${API_URL}/api/health`, {
                    headers: authHeaders(),
                });
                if (resp.ok) setHealth(await resp.json());
            } catch {
                /* ignore */
            }
        };
        fetchHealth();
        const interval = setInterval(fetchHealth, 10000);
        return () => clearInterval(interval);
    }, []);

    // Poll vehicle list
    useEffect(() => {
        const fetchVehicles = async () => {
            try {
                const resp = await fetch(`${API_URL}/api/vehicle/list`, {
                    headers: authHeaders(),
                });
                if (resp.ok) {
                    const data = await resp.json();
                    const map = {};
                    (data.vehicles || []).forEach((v) => {
                        map[v.vehicle_id] = v;
                    });
                    setVehicles((prev) => ({ ...prev, ...map }));
                }
            } catch {
                /* ignore */
            }
        };
        fetchVehicles();
        const interval = setInterval(fetchVehicles, 15000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="dashboard">
            {/* ── Top Bar ───────────────────────────────────── */}
            <header className="topbar">
                <div className="topbar-brand">
                    <div className="logo">V2X</div>
                    <h2>SmartV2X-CP Ultra</h2>
                </div>
                <div className="topbar-right">
                    <div className="ws-status">
                        <div className={`ws-dot ${wsConnected ? '' : 'disconnected'}`} />
                        {wsConnected ? 'Live' : 'Disconnected'}
                    </div>
                    <div className="user-info">
                        <span>{user?.name || 'User'}</span>
                        <span className="user-role">{user?.role || 'viewer'}</span>
                    </div>
                    <button className="btn-logout" onClick={logout}>
                        Sign Out
                    </button>
                </div>
            </header>

            {/* ── Main Grid ────────────────────────────────── */}
            <div className="dashboard-content">
                {/* Left: Map */}
                <div className="panel map-panel">
                    <div className="panel-header">
                        <h3>
                            🗺️ Live Vehicle Map
                        </h3>
                        <span className="badge badge-live">● LIVE</span>
                    </div>
                    <VehicleMap vehicles={vehicles} />
                </div>

                {/* Right: Alerts */}
                <div className="panel">
                    <div className="panel-header">
                        <h3>⚠️ Collision Alerts</h3>
                        <span className="badge badge-live">{alerts.length}</span>
                    </div>
                    <div className="panel-body">
                        <AlertPanel alerts={alerts} />
                    </div>
                </div>

                {/* Right: Health */}
                <div className="panel">
                    <div className="panel-header">
                        <h3>📡 System Health</h3>
                    </div>
                    <div className="panel-body">
                        <HealthPanel health={health} vehicleCount={Object.keys(vehicles).length} />
                    </div>
                </div>

                {/* Bottom Row */}
                <div className="bottom-row">
                    <div className="panel">
                        <div className="panel-header">
                            <h3>📊 Network Latency</h3>
                        </div>
                        <LatencyGraph latencyData={latencyData} />
                    </div>

                    <div className="panel">
                        <div className="panel-header">
                            <h3>🔗 Vehicle Pairing</h3>
                            <span className="badge badge-live">{Object.keys(vehicles).length} devices</span>
                        </div>
                        <div className="panel-body">
                            <PairingStatus vehicles={vehicles} />
                        </div>
                    </div>

                    {/* Admin-only panel */}
                    {user?.role === 'admin' && (
                        <div className="panel">
                            <div className="panel-header">
                                <h3>🛠️ Admin Controls</h3>
                            </div>
                            <div className="panel-body">
                                <div className="stats-grid">
                                    <div className="stat-card">
                                        <div className="label">WS Clients</div>
                                        <div className="value cyan">1</div>
                                    </div>
                                    <div className="stat-card">
                                        <div className="label">API Rate</div>
                                        <div className="value green">OK</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
