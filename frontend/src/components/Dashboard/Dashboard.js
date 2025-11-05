// src/components/Dashboard/Dashboard.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/http';

export default function Dashboard() {
  const [counts, setCounts] = useState({ usuarios: 0, solicitudes: 0, roles: 0 });

  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        const [u, s, r] = await Promise.all([
          api.get('/users/'),
          api.get('/solicitudes/'),
          api.get('/roles/'),
        ]);
        const users = Array.isArray(u.data) ? u.data : (u.data?.results || []);
        const sols  = Array.isArray(s.data) ? s.data : (s.data?.results || []);
        const roles = Array.isArray(r.data) ? r.data : (r.data?.results || []);
        setCounts({ usuarios: users.length, solicitudes: sols.length, roles: roles.length });
      } catch {
        setCounts({ usuarios: 0, solicitudes: 0, roles: 0 });
      }
    };
    load();
  }, []);

  return (
    <div className="dashboard" style={{maxWidth: 720}}>
      <h2 style={{textAlign:'center'}}>Dashboard</h2>
      <div className="dashboard-cards" style={{display:'grid', gap:16}}>
        <div className="card"><h3>Usuarios Registrados</h3><p>{counts.usuarios}</p></div>
        <div className="card"><h3>Solicitudes de Crédito</h3><p>{counts.solicitudes}</p></div>
        <div className="card"><h3>Roles Configurados</h3><p>{counts.roles}</p></div>
      </div>

      {/* Botón para gestionar empresas */}
      <div style={{marginTop:16, textAlign:'center'}}>
        <button onClick={() => navigate('/vista-empresas')}>Gestionar empresa</button>
      </div>
    </div>
  );
}
