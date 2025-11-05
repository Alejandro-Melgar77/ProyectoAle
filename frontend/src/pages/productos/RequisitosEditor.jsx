// src/pages/productos/RequisitosEditor.jsx
import React, { useEffect, useState } from 'react';
import { getProductos } from '../../services/productos';
import { listDocumentoTipos } from '../../services/documentos';
import { listRequisitos, createRequisito, updateRequisito, deleteRequisito } from '../../services/requisitos';

const TIPOS = ['PUBLICO','PRIVADO','INDEPENDIENTE'];

export default function RequisitosEditor() {
  const [productos, setProductos] = useState([]);
  const [docTipos, setDocTipos] = useState([]);
  const [producto, setProducto] = useState('');
  const [tipo, setTipo] = useState('');
  const [rows, setRows] = useState([]);
  const [adding, setAdding] = useState({ documento:'', obligatorio:true });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [p, d] = await Promise.all([getProductos(), listDocumentoTipos()]);
        setProductos(p);
        setDocTipos(d);
      } catch (e) { setErr('No se pudieron cargar catálogos.'); }
    })();
  }, []);

  const load = async () => {
    if (!producto || !tipo) { setRows([]); return; }
    setBusy(true);
    try {
      const data = await listRequisitos({ producto, tipo_trabajador: tipo });
      setRows(data);
    } finally { setBusy(false); }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [producto, tipo]);

  const onAdd = async (e) => {
    e.preventDefault();
    if (!producto || !tipo || !adding.documento) return;
    setBusy(true);
    try {
      await createRequisito({
        producto: Number(producto),
        tipo_trabajador: tipo,
        documento: Number(adding.documento),
        obligatorio: !!adding.obligatorio
      });
      setAdding({ documento:'', obligatorio:true });
      await load();
    } catch (e) { setErr('No se pudo crear el requisito'); }
    finally { setBusy(false); }
  };

  const toggleOblig = async (r) => {
    setBusy(true);
    try {
      await updateRequisito(r.id, { obligatorio: !r.obligatorio });
      await load();
    } finally { setBusy(false); }
  };

  const remove = async (r) => {
    if (!window.confirm('¿Eliminar este requisito?')) return;
    setBusy(true);
    try {
      await deleteRequisito(r.id);
      await load();
    } finally { setBusy(false); }
  };

  return (
    <div style={{maxWidth:900}}>
      <h2>Editor de requisitos por producto</h2>

      <div className="panel" style={{display:'grid',gridTemplateColumns:'1fr 1fr', gap:12}}>
        <div>
          <label>Producto</label>
          <select value={producto} onChange={e=>setProducto(e.target.value)}>
            <option value="">-- Selecciona --</option>
            {productos.map(p=> <option key={p.id} value={p.id}>{p.nombre} ({p.tipo})</option>)}
          </select>
        </div>
        <div>
          <label>Tipo de Trabajador</label>
          <select value={tipo} onChange={e=>setTipo(e.target.value)}>
            <option value="">-- Selecciona --</option>
            {TIPOS.map(t=> <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      {!!producto && !!tipo && (
        <>
          <div className="panel">
            <h4>Requisitos configurados</h4>
            {busy ? <div>Cargando…</div> : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Documento</th>
                    <th>Vigencia (días)</th>
                    <th>Obligatorio</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(r=>(
                    <tr key={r.id}>
                      <td>{r.documento?.nombre} <span style={{opacity:.6}}>({r.documento?.codigo})</span></td>
                      <td>{r.documento?.vigencia_dias ?? '-'}</td>
                      <td>
                        <button className={`badge ${r.obligatorio?'bg-success':'bg-secondary'}`} onClick={()=>toggleOblig(r)}>
                          {r.obligatorio ? 'Sí' : 'No'}
                        </button>
                      </td>
                      <td>
                        <button className="badge bg-danger" onClick={()=>remove(r)}>Eliminar</button>
                      </td>
                    </tr>
                  ))}
                  {!rows.length && <tr><td colSpan={4}>Sin requisitos aún</td></tr>}
                </tbody>
              </table>
            )}
          </div>

          <form onSubmit={onAdd} className="panel" style={{display:'grid',gridTemplateColumns:'2fr 1fr 1fr', gap:12}}>
            <select value={adding.documento} onChange={e=>setAdding(a=>({...a, documento:e.target.value}))} required>
              <option value="">-- Añadir documento --</option>
              {docTipos.map(d=> <option key={d.id} value={d.id}>{d.nombre} ({d.codigo})</option>)}
            </select>
            <label style={{display:'flex',alignItems:'center',gap:8}}>
              <input type="checkbox" checked={adding.obligatorio} onChange={e=>setAdding(a=>({...a, obligatorio:e.target.checked}))}/>
              Obligatorio
            </label>
            <button className="btn" disabled={busy}>Agregar</button>
          </form>
        </>
      )}

      {err && <div style={{color:'crimson'}}>{err}</div>}

      <style>{`
        .panel { background:#fff; padding:12px; border-radius:8px; margin:12px 0; }
        select { padding:8px; border:1px solid #ddd; border-radius:6px; width:100%; }
        .table { width:100%; border-collapse:collapse; }
        .table th, .table td { border-bottom:1px solid #eee; padding:8px; text-align:left; }
        .btn { background:#198754;color:#fff;border:none;border-radius:6px;padding:8px 12px; }
        .badge { padding:6px 10px; border:none; border-radius:12px; color:#fff; cursor:pointer; }
        .bg-success { background:#198754; }
        .bg-secondary { background:#6c757d; }
        .bg-danger { background:#dc3545; }
      `}</style>
    </div>
  );
}
