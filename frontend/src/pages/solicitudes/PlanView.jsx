// src/pages/solicitudes/PlanView.jsx
import React, { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { generarPlan, getPlan, downloadPlan } from '../../services/plan';

export default function PlanView() {
  const { id: solicitudId } = useParams();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [genBusy, setGenBusy] = useState(false);
  const [genErr, setGenErr] = useState('');

  const reload = async () => {
    setErr('');
    setLoading(true);
    try {
      const data = await getPlan(solicitudId);
      setPlan(data);
    } catch {
      setPlan(null);
      setErr('Sin plan generado aún.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { reload(); }, [solicitudId]);

  const doGenerar = async (overwrite = false) => {
    setGenErr('');
    setGenBusy(true);
    try {
      await generarPlan(solicitudId, { overwrite });
      await reload();
    } catch (e) {
      setGenErr(e?.response?.data?.detail || 'Error al generar plan');
    } finally {
      setGenBusy(false);
    }
  };

  const doExport = async (fmt) => {
    try {
      await downloadPlan(solicitudId, fmt); // 'pdf' | 'xlsx'
    } catch {
      setErr('No se pudo exportar el plan.');
    }
  };

  const totales = useMemo(() => {
    if (!plan) return null;
    return {
      capital: Number(plan.total_capital || 0).toFixed(2),
      interes: Number(plan.total_interes || 0).toFixed(2),
      cuotas: Number(plan.total_cuotas || 0).toFixed(2),
    };
  }, [plan]);

  return (
    <div>
      <h2>Plan de Pagos — Solicitud {solicitudId}</h2>

      <div className="panel">
        <button onClick={() => doGenerar(false)} disabled={genBusy}>Generar</button>
        <button onClick={() => doGenerar(true)}  disabled={genBusy} title="Recalcular y sobrescribir">
          Regenerar (overwrite)
        </button>
        <button onClick={() => doExport('pdf')}  disabled={!plan}>Exportar PDF</button>
        <button onClick={() => doExport('xlsx')} disabled={!plan}>Exportar XLSX</button>
        {genErr && <div className="err">{genErr}</div>}
      </div>

      {loading && <div>Cargando…</div>}
      {err && !plan && <div style={{ color: '#6c757d' }}>{err}</div>}

      {plan && (
        <>
          <div className="card">
            <div><b>Método:</b> {plan.metodo}</div>
            <div><b>Moneda:</b> {plan.moneda}</div>
            <div><b>Primera cuota:</b> {plan.primera_cuota_fecha}</div>
          </div>

          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>#</th><th>Vencimiento</th><th>Capital</th><th>Interés</th><th>Cuota</th><th>Saldo</th>
                </tr>
              </thead>
              <tbody>
                {plan.cuotas?.map((c) => (
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
              <tfoot>
                <tr>
                  <th colSpan={2} style={{ textAlign: 'right' }}>Totales</th>
                  <th>{totales.capital}</th>
                  <th>{totales.interes}</th>
                  <th>{totales.cuotas}</th>
                  <th></th>
                </tr>
              </tfoot>
            </table>
          </div>
        </>
      )}

      <style>{`
        .panel { background:#fff; padding:12px; border-radius:8px; display:flex; gap:8px; align-items:center; margin-bottom:12px; }
        .panel button { background:#0d6efd; color:#fff; border:none; border-radius:6px; padding:8px 12px; }
        .card { background:#fff; padding:12px; border-radius:8px; margin-bottom:12px; display:grid; gap:4px; }
        .table-wrap { overflow:auto; }
        .table { width:100%; border-collapse:collapse; background:#fff; }
        .table th, .table td { border-bottom:1px solid #eee; padding:8px; text-align:left; }
        .err { color:crimson; }
      `}</style>
    </div>
  );
}
