import { createContext, useContext, useEffect, useState } from 'react';
import http from '../api/http';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);  // opcional: info de /api/users/me/
  const [isAuth, setIsAuth] = useState(!!localStorage.getItem('access'));
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuth) {
      // opcional: cargar perfil / rol / cliente_id
      http.get('/api/users/me/')
        .then(res => setUser(res.data))
        .catch(() => setUser(null));
    }
  }, [isAuth]);

  const login = async (username, password) => {
    const { data } = await http.post('/api/auth/login/', { username, password });
    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    setIsAuth(true);
  };

  const logout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    setUser(null);
    setIsAuth(false);
  };

  return (
    <AuthContext.Provider value={{ isAuth, user, setUser, login, logout, loading, setLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
