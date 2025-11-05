// src/pages/solicitudes/Simulador.jsx
import React, { useState } from 'react';
import { simular } from '../../services/simulador';

export default function Simulador() {
  const [monto, setMonto] = useState(85000);
  const [plazo, setPlazo] = useState(48);
  const [tna, setTna] = useState(12.49);
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    // Validaciones simples en front
    if (!monto || monto <= 0) return setError('El monto debe ser mayor a 0.');
    if (!plazo || plazo < 1) return setError('El plazo debe ser al menos 1 mes.');
    if (!tna || tna <= 0) return setError('La TNA debe ser mayor a 0.');

    setBusy(true);
    try {
      const res = await simular({
        monto: Number(monto),
        plazo_meses: Number(plazo),
        tasa_nominal_anual: Number(tna),
      });
      setData(res);
    } catch (err) {
      // Mensaje legible al usuario
      const apiMsg =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err?.message ||
        'No se pudo calcular la simulación.';
      setError(String(apiMsg));
      setData(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <h2 style={{ marginBottom: 12 }}>Simulador de Crédito</h2>

      <form
        onSubmit={onSubmit}
        className="panel"
        style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(3, 1fr)' }}
      >
        <label className="field">
          <span>Monto</span>
          <input
            type="number"
            className="input"
            value={monto}
            onChange={(e) => setMonto(+e.target.value)}
            placeholder="Ej: 85000"
            aria-label="Monto a financiar"
          />
        </label>

        <label className="field">
          <span>Plazo (meses)</span>
          <input
            type="number"
            className="input"
            value={plazo}
            onChange={(e) => setPlazo(+e.target.value)}
            placeholder="Ej: 48"
            aria-label="Plazo en meses"
          />
        </label>

        <label className="field">
          <span>TNA (%)</span>
          <input
            type="number"
            step="0.01"
            className="input"
            value={tna}
            onChange={(e) => setTna(+e.target.value)}
            placeholder="Ej: 12.49"
            aria-label="Tasa nominal anual"
          />
        </label>

        <button className="btn" disabled={busy} style={{ gridColumn: '1 / -1' }}>
          {busy ? 'Calculando…' : 'Simular'}
        </button>

        {data?.resumen && (
        <div className="panel" style={{display:'grid',gridTemplateColumns:'repeat(5,1fr)',gap:12,marginBottom:12}}>
            <div>
            <div style={{fontSize:12,color:'#6c757d'}}>Moneda</div>
            <div style={{fontWeight:700}}>{data.resumen.moneda || 'BOB'}</div>
            </div>
            <div>
            <div style={{fontSize:12,color:'#6c757d'}}>Cuota (ref.)</div>
            <div style={{fontWeight:700}}>
                {Number(data.resumen.cuota ?? 0).toFixed(2)}
            </div>
            </div>
            <div>
            <div style={{fontSize:12,color:'#6c757d'}}>Total capital</div>
            <div style={{fontWeight:700}}>
                {Number(data.resumen.total_capital ?? 0).toFixed(2)}
            </div>
            </div>
            <div>
            <div style={{fontSize:12,color:'#6c757d'}}>Total interés</div>
            <div style={{fontWeight:700}}>
                {Number(data.resumen.total_interes ?? 0).toFixed(2)}
            </div>
            </div>
            <div>
            <div style={{fontSize:12,color:'#6c757d'}}>Total a pagar</div>
            <div style={{fontWeight:700}}>
                {Number(data.resumen.total_cuotas ?? 0).toFixed(2)}
            </div>
            </div>
            {/* Línea inferior con el ajuste total si aplica */}
            <div style={{gridColumn:'1 / -1',marginTop:6,fontSize:12,color:'#6c757d'}}>
            Ajuste por redondeo: <b>{Number(data.resumen.redondeo_ajuste_total ?? 0).toFixed(2)}</b>
            </div>
        </div>
        )}

      </form>

      {error && (
        <div className="panel" style={{ color: 'crimson' }}>
          {error}
        </div>
      )}

      {data && (
        <div className="panel">
          {data.resumen?.cuota != null && (
            <div style={{ marginBottom: 8 }}>
              Cuota estimada:{' '}
              <b>{Number(data.resumen.cuota).toFixed(2)}</b>
            </div>
          )}
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Vencimiento</th>
                  <th>Capital</th>
                  <th>Interés</th>
                  <th>Cuota</th>
                  <th>Saldo</th>
                </tr>
              </thead>
              <tbody>
                {data.cuotas?.map((c) => (
                  <tr key={c.nro_cuota}>
                    <td>{c.nro_cuota}</td>
                    <td>{c.fecha_vencimiento}</td>
                    <td>{Number(c.capital).toFixed(2)}</td>
                    <td>{Number(c.interes).toFixed(2)}</td>
                    <td>{Number(c.cuota).toFixed(2)}</td>
                    <td>{Number(c.saldo).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <style>{`
        .panel { background:#fff; padding:12px; border-radius:10px; margin:12px 0; }
        .field { display:flex; flex-direction:column; gap:6px; }
        .input { padding:8px; border:1px solid #ddd; border-radius:6px; }
        .btn { background:#0d6efd; color:#fff; border:none; border-radius:6px; padding:8px 12px; }
        .table-wrap { overflow:auto; }
        .table { width:100%; border-collapse:collapse; background:#fff; }
        .table th, .table td { border-bottom:1px solid #eee; padding:8px; text-align:left; }
      `}</style>
    </div>
  );
}
