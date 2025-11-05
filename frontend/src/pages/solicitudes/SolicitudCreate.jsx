// src/pages/solicitudes/SolicitudCreate.jsx
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { fetchClientes } from '../../services/clientes';
import { createSolicitud } from '../../services/solicitudes';
import { getProductos, getRequisitos } from '../../services/productos';

const TIPOS_TRAB = ['PUBLICO', 'PRIVADO', 'INDEPENDIENTE'];

export default function SolicitudCreate() {
  const nav = useNavigate();

  // catálogos
  const [clientes, setClientes] = useState([]);
  const [productos, setProductos] = useState([]);
  const [loadingClientes, setLoadingClientes] = useState(true);
  const [loadingProductos, setLoadingProductos] = useState(true);
  const [errCli, setErrCli] = useState('');
  const [errProd, setErrProd] = useState('');

  // selección
  const [clienteId, setClienteId] = useState('');
  const [productoId, setProductoId] = useState('');
  const [tipoTrab, setTipoTrab] = useState('');

  // derivados
  const productoSel = useMemo(
    () => productos.find(p => String(p.id) === String(productoId)),
    [productos, productoId]
  );
  const tipoCredito = productoSel?.tipo || '';

  // requisitos dinámicos
  const [requisitos, setRequisitos] = useState([]);
  const [loadingReq, setLoadingReq] = useState(false);
  const [errorReq, setErrorReq] = useState('');

  // datos de crédito (opcionales)
  const [mostrarDatosCredito, setMostrarDatosCredito] = useState(false);
  const [monto, setMonto] = useState('');
  const [plazo, setPlazo] = useState('');
  const [tna, setTna] = useState('24.0');
  const [moneda, setMoneda] = useState('BOB');

  // submit
  const [submitting, setSubmitting] = useState(false);
  const [errSubmit, setErrSubmit] = useState('');

  // =======================
  // Cargar catálogos
  // =======================
  useEffect(() => {
    (async () => {
      try {
        const cs = await fetchClientes();
        setClientes(cs || []);
      } catch {
        setErrCli('No se pudieron cargar clientes.');
      } finally {
        setLoadingClientes(false);
      }
    })();

    (async () => {
      try {
        const ps = await getProductos();
        setProductos(ps || []);
      } catch {
        setErrProd('No se pudieron cargar productos.');
      } finally {
        setLoadingProductos(false);
      }
    })();
  }, []);

  // =======================
  // Cargar requisitos
  // =======================
  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!productoId || !tipoTrab) {
        setRequisitos([]);
        return;
      }
      setLoadingReq(true);
      setErrorReq('');
      try {
        const items = await getRequisitos(productoId, tipoTrab); // GET /productos/:id/requisitos/?tipo_trabajador=...
        if (!cancelled) setRequisitos(items || []);
      } catch (e) {
        console.error(e);
        if (!cancelled) {
          setErrorReq('Error al cargar requisitos.');
          setRequisitos([]);
        }
      } finally {
        if (!cancelled) setLoadingReq(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [productoId, tipoTrab]);

  // =======================
  // Crear solicitud
  // =======================
  const onCrear = async () => {
    setErrSubmit('');

    // Validación mínima de UI
    if (!clienteId) return setErrSubmit('Selecciona un cliente.');
    if (!productoId) return setErrSubmit('Selecciona un producto.');
    if (!tipoTrab)  return setErrSubmit('Selecciona un tipo de trabajador.');

    setSubmitting(true);
    try {
      const payload = {
        cliente: Number(clienteId),
        producto: Number(productoId),
        tipo_trabajador: tipoTrab,     // 'PUBLICO' | 'PRIVADO' | 'INDEPENDIENTE'
        tipo_credito: tipoCredito || undefined, // si tu modelo lo admite

        // Si tu serializer exige estos campos, envíalos con defaults razonables
        monto: monto ? Number(monto) : 1,
        plazo_meses: plazo ? Number(plazo) : 1,
        tasa_nominal_anual: tna ? Number(tna) : 0,
        moneda: moneda || 'BOB',
      };

      const s = await createSolicitud(payload); // POST /api/solicitudes/
      // Navegar directo al checklist (CU19/CU13)
      nav(`/solicitudes/${s.id}/checklist`);
    } catch (e) {
      console.error(e);
      // intenta mostrar mensaje del backend
      const apiMsg =
        e?.response?.data?.detail ||
        e?.response?.data?.non_field_errors?.[0] ||
        JSON.stringify(e?.response?.data || {});
      setErrSubmit(apiMsg || 'No se pudo crear la solicitud.');
    } finally {
      setSubmitting(false);
    }
  };

  // =======================
  // UI
  // =======================
  return (
    <div style={{ maxWidth: 820 }}>
      <h2>Nueva Solicitud</h2>

      {/* Cliente */}
      <div className="panel">
        <label>Cliente</label>
        {loadingClientes ? (
          <div>Cargando clientes…</div>
        ) : (
          <select
            className="input"
            value={clienteId}
            onChange={e => setClienteId(e.target.value)}
          >
            <option value="">-- Selecciona --</option>
            {clientes.map(c => (
              <option key={c.id} value={c.id}>
                {(c.user_info?.first_name || '')} {(c.user_info?.last_name || '')} — #{c.id}
              </option>
            ))}
          </select>
        )}
        {errCli && <div style={{ color: 'crimson' }}>{errCli}</div>}
      </div>

      {/* Producto */}
      <div className="panel">
        <label>Producto</label>
        {loadingProductos ? (
          <div>Cargando productos…</div>
        ) : (
          <select
            className="input"
            value={productoId}
            onChange={e => setProductoId(e.target.value)}
          >
            <option value="">-- Selecciona --</option>
            {productos.map(p => (
              <option key={p.id} value={p.id}>
                {p.nombre} ({p.tipo})
              </option>
            ))}
          </select>
        )}
        {errProd && <div style={{ color: 'crimson' }}>{errProd}</div>}
      </div>

      {/* Tipo de trabajador */}
      <div className="panel">
        <label>Tipo de Trabajador</label>
        <select
          className="input"
          value={tipoTrab}
          onChange={e => setTipoTrab(e.target.value)}
        >
          <option value="">-- Selecciona --</option>
          {TIPOS_TRAB.map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* Requisitos dinámicos */}
      {!!productoId && !!tipoTrab && (
        <div className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0 }}>Documentos requeridos</h3>
            <div style={{ opacity: .7 }}>
              Tipo de crédito: <b>{tipoCredito || '-'}</b>
            </div>
          </div>

          {loadingReq && <div>Cargando requisitos…</div>}
          {errorReq && <div style={{ color: 'crimson' }}>{errorReq}</div>}

          {!loadingReq && requisitos.length === 0 && !errorReq && (
            <div>No hay requisitos configurados para esta combinación.</div>
          )}

          {requisitos.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Documento</th>
                  <th>Obligatorio</th>
                  <th>Vigencia (días)</th>
                </tr>
              </thead>
              <tbody>
                {requisitos.map((r, idx) => (
                  <tr key={idx}>
                    <td>
                      {r.documento?.nombre}{' '}
                      <small style={{ color: '#6c757d' }}>
                        ({r.documento?.codigo})
                      </small>
                    </td>
                    <td>{r.obligatorio ? 'Sí' : 'No'}</td>
                    <td>{r.documento?.vigencia_dias ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Acciones */}
          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <button
              type="button"
              className="btn"
              onClick={() => setMostrarDatosCredito(v => !v)}
            >
              {mostrarDatosCredito ? 'Ocultar datos de crédito' : 'Completar datos de crédito'}
            </button>
            <button
              type="button"
              className="btn btn-success"
              onClick={onCrear}
              disabled={!clienteId || !productoId || !tipoTrab || submitting}
            >
              {submitting ? 'Creando…' : 'Crear y ver checklist'}
            </button>
          </div>
        </div>
      )}

      {/* Datos financieros opcionales */}
      {mostrarDatosCredito && (
        <div
          className="panel"
          style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(4, 1fr)' }}
        >
          <label className="field">
            <span>Monto</span>
            <input
              className="input"
              type="number"
              value={monto}
              onChange={e => setMonto(e.target.value)}
              min="0"
            />
          </label>
          <label className="field">
            <span>Plazo (meses)</span>
            <input
              className="input"
              type="number"
              value={plazo}
              onChange={e => setPlazo(e.target.value)}
              min="1"
            />
          </label>
          <label className="field">
            <span>TNA (%)</span>
            <input
              className="input"
              type="number"
              step="0.01"
              value={tna}
              onChange={e => setTna(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Moneda</span>
            <select
              className="input"
              value={moneda}
              onChange={e => setMoneda(e.target.value)}
            >
              <option value="BOB">BOB</option>
              <option value="USD">USD</option>
            </select>
          </label>
        </div>
      )}

      {errSubmit && <div style={{ color: 'crimson', marginTop: 8 }}>{errSubmit}</div>}

      <style>{`
        .panel { background:#fff; padding:12px; border-radius:10px; margin:12px 0; }
        .input { width:100%; padding:8px; border:1px solid #ddd; border-radius:6px; }
        .table { width:100%; border-collapse:collapse; }
        .table th, .table td { border-bottom:1px solid #eee; padding:8px; text-align:left; }
        .btn { background:#0d6efd; color:#fff; border:none; border-radius:6px; padding:8px 12px; cursor:pointer; }
        .btn-success { background:#198754; }
        .field { display:flex; flex-direction:column; gap:6px; }
      `}</style>
    </div>
  );
}
