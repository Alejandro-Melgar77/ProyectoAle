// src/components/Auth/RequireAuth.jsx
import { Navigate, useLocation } from 'react-router-dom';

export default function RequireAuth({ authed, loading, children }) {
  const loc = useLocation();
  if (loading) return <div style={{ padding: 24 }}>Verificando sesión…</div>;
  if (!authed) return <Navigate to="/login" state={{ from: loc }} replace />;
  return children;
}
