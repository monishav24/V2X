/**
 * SmartV2X-CP Ultra — Auth Context
 * React context for authentication state management.
 */
import React, { createContext, useContext, useState, useEffect } from 'react';
import { getStoredToken, getStoredUser, storeAuth, clearAuth } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const savedToken = getStoredToken();
        const savedUser = getStoredUser();
        if (savedToken && savedUser) {
            setToken(savedToken);
            setUser(savedUser);
        }
        setLoading(false);
    }, []);

    const handleLogin = (tokenData) => {
        const userData = {
            name: tokenData.name,
            role: tokenData.role,
        };
        storeAuth(tokenData.access_token, userData);
        setToken(tokenData.access_token);
        setUser(userData);
    };

    const handleLogout = () => {
        clearAuth();
        setToken(null);
        setUser(null);
    };

    if (loading) return null;

    return (
        <AuthContext.Provider value={{ user, token, login: handleLogin, logout: handleLogout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
}
