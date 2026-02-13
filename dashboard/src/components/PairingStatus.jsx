/**
 * SmartV2X-CP Ultra — Vehicle Pairing Status
 */
import React from 'react';

export default function PairingStatus({ vehicles = {} }) {
    const list = Object.values(vehicles);

    if (list.length === 0) {
        return (
            <div className="empty-state">
                <div className="icon">🚗</div>
                <p>No vehicles paired</p>
                <p style={{ fontSize: 12 }}>Waiting for OBU connections</p>
            </div>
        );
    }

    return (
        <div className="vehicle-list">
            {list.map((v) => {
                const isOnline = v.status === 'online';
                const riskLevel = (v.risk?.level || 'LOW').toUpperCase();

                return (
                    <div key={v.vehicle_id} className="vehicle-item">
                        <div className="vehicle-info">
                            <div className={`vehicle-dot ${isOnline ? 'online' : 'offline'}`} />
                            <div>
                                <div className="vehicle-name">{v.vehicle_id}</div>
                                <div className="vehicle-status">
                                    {isOnline ? 'Online' : 'Offline'}
                                    {v.device_name ? ` · ${v.device_name}` : ''}
                                </div>
                            </div>
                        </div>
                        <span className={`risk-badge ${riskLevel.toLowerCase()}`}>
                            {riskLevel}
                        </span>
                    </div>
                );
            })}
        </div>
    );
}
