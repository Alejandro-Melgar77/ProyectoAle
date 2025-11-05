import React, { useEffect, useMemo, useState } from 'react';
import { listSolicitudes } from '../../services/solicitudes';
import { Link } from 'react-router-dom';

const ESTADOS = ['TODOS', 'DRAFT', 'ENVIADA', 'EVALUADA', 'APROBADA', 'RECHAZADA'];

export default function SolicitudesList() {
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState([]);
  const [err, setErr] = useState('');

  const [q, setQ] = useState('');              // búsqueda
  const [estado, setEstado] = useState('TODOS'); // filtro estado

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        const data = await listSolicitudes();
        if (!mounted) return;
        setRows(data);
      } catch (e) {
        setErr('No se pudo cargar solicitudes');
      } finally {
        setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const filtered = useMemo(() => {
    const qn = q.trim().toLowerCase();
    return rows.filter((r) => {
      const matchEstado = estado === 'TODOS' ? true : (r.estado || '').toUpperCase() === estado;

      const nombre =
        r.cliente_panel?.nombre
        || `${r.cliente_info?.user_info?.first_name || ''} ${r.cliente_info?.user_info?.last_name || ''}`.trim()
        || r.cliente_nombre
        || `Cliente #${r.cliente}`;

      const doc =
        r.cliente_panel?.documento
        || r.cliente_info?.numero_documento
        || '';

      const matchQ =
        !qn ||
        nombre.toLowerCase().includes(qn) ||
        doc.toLowerCase().includes(qn) ||
        (r.id || '').toLowerCase().includes(qn);

      return matchEstado && matchQ;
    });
  }, [rows, estado, q]);

  return (
    <div>
      <h2>Solicitudes</h2>

      <div className="toolbar">
        <div className="left">
          <input
            className="input"
            placeholder="Buscar por cliente, documento o ID…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select className="input" value={estado} onChange={(e) => setEstado(e.target.value)}>
            {ESTADOS.map((x) => (
              <option key={x} value={x}>{x}</option>
            ))}
          </select>
        </div>
        <Link className="btn" to="/solicitudes/nueva">+ Nueva solicitud</Link>
      </div>

      {loading && <div>Cargando...</div>}
      {err && <div style={{ color: 'crimson' }}>{err}</div>}
      {!loading && !filtered.length && <div>No hay solicitudes que coincidan.</div>}

      {!!filtered.length && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th><th>Cliente</th><th>Doc.</th>
                <th>Monto</th><th>Plazo</th><th>Tasa</th>
                <th>Estado</th><th>Creada</th><th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const nombre =
                  r.cliente_panel?.nombre
                  || `${r.cliente_info?.user_info?.first_name || ''} ${r.cliente_info?.user_info?.last_name || ''}`.trim()
                  || r.cliente_nombre
                  || `Cliente #${r.cliente}`;

                const doc =
                  r.cliente_panel?.documento
                  || r.cliente_info?.numero_documento
                  || '';

                return (
                  <tr key={r.id}>
                    <td style={{ fontFamily: 'monospace' }}>{r.id}</td>
                    <td>{nombre}</td>
                    <td>{doc || '—'}</td>
                    <td>{r.monto}</td>
                    <td>{r.plazo_meses}</td>
                    <td>{r.tasa_nominal_anual}%</td>
                    <td><strong>{r.estado}</strong></td>
                    <td>{new Date(r.created_at).toLocaleString()}</td>
                    <td><Link className="btn" to={`/solicitudes/${r.id}`}>Ver</Link></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <style>{`
        .toolbar { display:flex; justify-content:space-between; align-items:center; margin:12px 0; gap:12px; }
        .left { display:flex; gap:8px; }
        .input { padding:8px; border:1px solid #ddd; border-radius:6px; }
        .btn { background:#198754;color:#fff;padding:8px 12px;border-radius:6px;text-decoration:none; }
        .table-wrap { overflow:auto; }
        .table { width:100%; border-collapse: collapse; background:#fff; border-radius:8px; }
        .table th, .table td { padding:10px; border-bottom:1px solid #eee; text-align:left; }
      `}</style>
    </div>
  );
}
