// src/components/Login/Login.js
import React, { useState } from 'react';
import axios from '../../config/axios';
import './Login.css';

const Login = ({ onLoginSuccess }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setCredentials({ ...credentials, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      // Usa la instancia y ruta relativa
      const { data } = await axios.post('/api/auth/login/', credentials);
      const { access, refresh } = data;

      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      // Como ya tenemos interceptor, no hace falta setear defaults aquí,
      // pero no hace daño si quieres mantenerlo:
      axios.defaults.headers.common['Authorization'] = `Bearer ${access}`;

      onLoginSuccess?.();
    } catch (err) {
      setError('Credenciales inválidas. Por favor, intente nuevamente.');
      console.error('Login error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>Iniciar Sesión</h2>
        {error && <div className="error-message">{error}</div>}
        <div className="form-group">
          <label htmlFor="username">Usuario:</label>
          <input id="username" name="username" value={credentials.username}
                 onChange={handleChange} required autoComplete="username" />
        </div>
        <div className="form-group">
          <label htmlFor="password">Contraseña:</label>
          <input type="password" id="password" name="password" value={credentials.password}
                 onChange={handleChange} required autoComplete="current-password" />
        </div>
        <button type="submit" className="login-button" disabled={isLoading}>
          {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
        </button>
      </form>
    </div>
  );
};

export default Login;
