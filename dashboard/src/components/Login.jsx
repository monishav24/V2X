/**
 * SmartV2X-CP Ultra — Login & Signup Component
 */
import React, { useState } from 'react';
import { login as apiLogin, register as apiRegister } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export default function Login() {
    const { login } = useAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccessMsg('');
        setLoading(true);
        try {
            if (isLogin) {
                const data = await apiLogin(username, password);
                login(data);
            } else {
                const data = await apiRegister(username, password, name);
                setSuccessMsg('Account created! Logging you in...');
                setTimeout(() => login(data), 1000);
            }
        } catch (err) {
            setError(err.message || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    const toggleMode = () => {
        setIsLogin(!isLogin);
        setError('');
        setSuccessMsg('');
        setUsername('');
        setPassword('');
        setName('');
    };

    return (
        <div className="login-container">
            <form className="login-card" onSubmit={handleSubmit}>
                <h1>SmartV2X-CP</h1>
                <p className="subtitle">
                    {isLogin ? 'Sign in to access the platform' : 'Create your account'}
                </p>

                {!isLogin && (
                    <div className="form-group">
                        <label htmlFor="name">Full Name (Optional)</label>
                        <input
                            id="name"
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Enter your name"
                        />
                    </div>
                )}

                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        id="username"
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Enter username"
                        autoComplete="username"
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter password"
                        autoComplete={isLogin ? "current-password" : "new-password"}
                        required
                    />
                </div>

                <button className="btn-primary" type="submit" disabled={loading}>
                    {loading ? 'Processing…' : (isLogin ? 'Sign In' : 'Create Account')}
                </button>

                {error && <p className="login-error">{error}</p>}
                {successMsg && <p className="login-success" style={{ color: 'green', textAlign: 'center', marginTop: 10 }}>{successMsg}</p>}

                <div className="login-footer" style={{ marginTop: 20, textAlign: 'center', fontSize: '0.9rem' }}>
                    <p>
                        {isLogin ? "Don't have an account? " : "Already have an account? "}
                        <button
                            type="button"
                            onClick={toggleMode}
                            style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontWeight: 'bold' }}
                        >
                            {isLogin ? 'Sign Up' : 'Log In'}
                        </button>
                    </p>
                </div>
            </form>
        </div>
    );
}
