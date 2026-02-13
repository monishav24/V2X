/**
 * SmartV2X-CP Ultra — System Health Panel
 */
import React from 'react';

export default function HealthPanel({ health = {}, vehicleCount = 0 }) {
    const uptime = health.uptime_seconds
        ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m`
        : '—';

    return (
        <div className="stats-grid">
            <div className="stat-card">
                <div className="label">Status</div>
                <div className={`value ${health.status === 'healthy' ? 'green' : 'red'}`}>
                    {health.status === 'healthy' ? '● Healthy' : '○ Down'}
                </div>
            </div>
            <div className="stat-card">
                <div className="label">Uptime</div>
                <div className="value cyan">{uptime}</div>
            </div>
            <div className="stat-card">
                <div className="label">Active Vehicles</div>
                <div className="value blue">{health.active_vehicles ?? vehicleCount}</div>
            </div>
            <div className="stat-card">
                <div className="label">Total Vehicles</div>
                <div className="value purple">{health.total_vehicles ?? 0}</div>
            </div>
            <div className="stat-card">
                <div className="label">Collision Events</div>
                <div className="value amber">{health.collision_events_total ?? 0}</div>
            </div>
            <div className="stat-card">
                <div className="label">Server Latency</div>
                <div className="value green">&lt; 60ms</div>
            </div>
        </div>
    );
}
