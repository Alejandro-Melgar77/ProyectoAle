// src/components/EmployeeManagement/EmployeeManagement.js
import React, { useEffect, useMemo, useState } from 'react';
import api from '../../api/http';
import './EmployeeManagement.css';

export default function EmployeeManagement() {
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const [filters, setFilters] = useState({
    q: '',
    departamento: '',
    puede_aprobar: '',
  });

  useEffect(() => {
    const load = async () => {
      setBusy(true); setErr('');
      try {
        const { data } = await api.get('/users/');
        const onlyEmployees = (Array.isArray(data) ? data : data?.results || [])
          .filter(u => !!u.empleado_info);
        setRows(onlyEmployees);
      } catch (e) {
        console.error('Fetch employees error:', e);
        setErr('Error al cargar los empleados');
        setRows([]);
      } finally {
        setBusy(false);
      }
    };
    load();
  }, []);

  const filtered = useMemo(() => {
    const q = filters.q.toLowerCase().trim();
    return rows.filter(u => {
      const ei = u.empleado_info || {};
      const ui = ei.user_info || u;

      const matchQ =
        ui.username?.toLowerCase().includes(q) ||
        ui.first_name?.toLowerCase().includes(q) ||
        ui.last_name?.toLowerCase().includes(q) ||
        ei.codigo_empleado?.toLowerCase().includes(q);

      const matchDep = !filters.departamento || ei.departamento === filters.departamento;

      const matchApr =
        filters.puede_aprobar === '' ||
        (filters.puede_aprobar === 'true' && ei.puede_aprobar_creditos) ||
        (filters.puede_aprobar === 'false' && !ei.puede_aprobar_creditos);

      return matchQ && matchDep && matchApr;
    });
  }, [rows, filters]);

  if (busy) return <div className="loading">Cargando empleados…</div>;

  return (
    <div className="employee-management-container">
      <h2>Gestión de Personal</h2>

      {err && <div className="error-message">{err}</div>}

      <div className="filters">
        <input
          type="text"
          name="q"
          placeholder="Buscar por nombre, usuario o código"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          className="search-input"
        />
        <select
          name="departamento"
          value={filters.departamento}
          onChange={(e) => setFilters({ ...filters, departamento: e.target.value })}
        >
          <option value="">Todos los departamentos</option>
          <option value="CREDITO">Crédito</option>
          <option value="ADMIN">Administración</option>
          <option value="TESORERIA">Tesorería</option>
          <option value="ATENCION">Atención al Cliente</option>
        </select>
        <select
          name="puede_aprobar"
          value={filters.puede_aprobar}
          onChange={(e) => setFilters({ ...filters, puede_aprobar: e.target.value })}
        >
          <option value="">Todos</option>
          <option value="true">Puede aprobar</option>
          <option value="false">No puede aprobar</option>
        </select>
      </div>

      <div className="employees-list">
        <h3>Lista de Empleados</h3>
        {filtered.length === 0 ? (
          <p>No hay empleados registrados.</p>
        ) : (
          <table className="employees-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Email</th>
                <th>Departamento</th>
                <th>Salario</th>
                <th>Supervisor</th>
                <th>Aprobar Créditos</th>
                <th>Límite</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(u => {
                const ei = u.empleado_info || {};
                const ui = ei.user_info || u;
                return (
                  <tr key={u.id}>
                    <td>{ei.codigo_empleado || '—'}</td>
                    <td>{ui.username}</td>
                    <td>{`${ui.first_name || ''} ${ui.last_name || ''}`.trim() || '—'}</td>
                    <td>{ui.email}</td>
                    <td>{ei.departamento || '—'}</td>
                    <td>{ei.salario ?? '—'}</td>
                    <td>{ei.es_supervisor ? 'Sí' : 'No'}</td>
                    <td>{ei.puede_aprobar_creditos ? 'Sí' : 'No'}</td>
                    <td>{ei.limite_aprobacion ?? '—'}</td>
                    <td>{ui.is_active ? 'Activo' : 'Inactivo'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
