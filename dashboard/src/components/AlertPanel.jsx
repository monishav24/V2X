/**
 * SmartV2X-CP Ultra — Alert Panel
 * Displays real-time collision alerts sorted by severity.
 */
import React from 'react';

const RISK_ICONS = {
    HIGH: '🔴',
    MEDIUM: '🟡',
    LOW: '🟢',
};

export default function AlertPanel({ alerts = [] }) {
    if (alerts.length === 0) {
        return (
            <div className="empty-state">
                <div className="icon">🛡️</div>
                <p>No active alerts</p>
                <p style={{ fontSize: 12 }}>System monitoring active</p>
            </div>
        );
    }

    return (
        <div style={{ maxHeight: 320, overflowY: 'auto' }}>
            {alerts.slice(0, 20).map((alert, idx) => {
                const level = alert.risk?.level || alert.risk_level || 'LOW';
                const time = alert.timestamp
                    ? new Date(alert.timestamp * 1000).toLocaleTimeString()
                    : '';

                return (
                    <div key={idx} className="alert-item">
                        <div className={`alert-icon ${level.toLowerCase()}`}>
                            {RISK_ICONS[level] || '⚪'}
                        </div>
                        <div className="alert-content">
                            <div className="title">
                                {level} Risk — {alert.vehicle_id || alert.data?.vehicle_id || 'Vehicle'}
                            </div>
                            <div className="details">
                                {alert.risk?.ttc != null && `TTC: ${alert.risk.ttc.toFixed(1)}s · `}
                                {alert.risk?.min_distance != null && `Dist: ${alert.risk.min_distance.toFixed(1)}m`}
                                {alert.details || ''}
                            </div>
                            {time && <div className="time">{time}</div>}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
