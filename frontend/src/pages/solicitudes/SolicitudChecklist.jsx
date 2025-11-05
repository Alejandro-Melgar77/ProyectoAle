import React, { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getChecklist } from '../../services/solicitudes';
import {
  subirDocumento,
  reemplazarDocumento,
  eliminarDocumento,
} from '../../services/documentos';
import { toAbsoluteUrl } from '../../utils/url';

// Mapa de códigos -> id de DocumentoTipo (según tus fixtures)
const DOC_MAP = {
  CI: 1, DOMICILIO: 2, BOLETAS_3M: 3, AFP_1M: 4, EXTRACTOS_6M: 5, CERT_TRABAJO: 6,
  PROFORMA_VEH: 7, FOLIO_REAL: 8, GRAVAMEN: 9, AVALUO: 10, NIT: 11, IVA_6M: 12,
};

export default function SolicitudChecklist() {
  const { id } = useParams();
  const solicitudId = id;

  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const refresh = async () => {
    try {
      setErr('');
      const data = await getChecklist(solicitudId);
      setItems(data || []);
    } catch (e) {
      console.error(e);
      setErr('No se pudo obtener el checklist.');
    }
  };

  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, [solicitudId]);

  const faltantes = useMemo(
    () => items.filter((i) => !i.recibido || i.valido === false),
    [items]
  );

  return (
    <div className="wrap">
      <h2>Checklist de Documentos — Solicitud {solicitudId}</h2>

      {err && <div className="panel warn">{err}</div>}

      <div className="list">
        {items.map((it) => (
          <RowItem
            key={it.codigo}
            item={it}
            solicitudId={solicitudId}
            onRefresh={refresh}
            globalBusy={busy}
            setGlobalBusy={setBusy}
          />
        ))}
      </div>

      <div className="panel">
        {faltantes.length === 0 ? (
          <div className="oktxt">
            Checklist completo. El oficial puede evaluar tu solicitud.
          </div>
        ) : (
          <div>
            Faltan documentos o hay observaciones. Sube / reemplaza para continuar.
          </div>
        )}
      </div>

      <style>{`
        .wrap { max-width: 980px; }
        .list { display: grid; gap: 12px; margin-top: 12px; }
        .card { background: #fff; border-radius: 10px; padding: 12px; }
        .row { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
        .title { font-weight: 600; }
        .muted { color: #64748b; }
        .meta { font-size: .9rem; color: #475569; }
        .badge { border: 1px solid #cbd5e1; border-radius: 999px; padding: 2px 10px; }
        .badge.ok { background: #dcfce7; border-color: #16a34a; color: #166534; }
        .badge.warn { background: #fef3c7; border-color: #d97706; color: #92400e; }
        .panel { margin-top: 12px; background: #fff; padding: 12px; border-radius: 10px; }
        .panel.warn { border: 1px solid #fca5a5; background: #fee2e2; color: #7f1d1d; }
        .oktxt { color: #166534; font-weight: 600; }
        .btn { background: #0d6efd; color: #fff; border: none; border-radius: 6px; padding: 8px 10px; }
        .btn.light { background: #e9ecef; color: #212529; }
        .btn.danger { background: #dc3545; }
        .inputs { display:flex; gap:8px; align-items:center; flex-wrap: wrap; }
        .input { padding:8px; border:1px solid #ddd; border-radius:6px; }
        .actions { display:flex; gap:8px; align-items:center; }
        .link { background: transparent; color: #0d6efd; text-decoration: underline; padding: 0; border:none; }
      `}</style>
    </div>
  );
}

function RowItem({ item, solicitudId, onRefresh, globalBusy, setGlobalBusy }) {
  const [file, setFile] = useState(null);
  const [fecha, setFecha] = useState(item.fecha_emision || '');
  const [localBusy, setLocalBusy] = useState(false);
  const recibido = !!item.recibido;
  const observ = recibido && item.valido === false;

  const disabled = globalBusy || localBusy;

  const docTipoId = item.documento_tipo_id || DOC_MAP[item.codigo];

  // para resetear input file visualmente luego de subir/reemplazar
  const [fileKey, setFileKey] = useState(0);
  const resetFileInput = () => { setFile(null); setFileKey(k => k + 1); };

  const subir = async () => {
    if (!file) return;
    if (!docTipoId) {
      alert(`Falta mapear ${item.codigo} -> id en DOC_MAP`);
      return;
    }
    setLocalBusy(true); setGlobalBusy(true);
    try {
      await subirDocumento({
        solicitudId,
        documentoTipoId: docTipoId,
        archivo: file,
        fecha_emision: fecha || undefined,
      });
      resetFileInput();
      await onRefresh();
    } catch (e) {
      console.error(e);
      alert('No se pudo subir el documento.');
    } finally {
      setLocalBusy(false); setGlobalBusy(false);
    }
  };

  const reemplazar = async () => {
    if (!file) return;
    if (!item.adjunto_id) return;
    setLocalBusy(true); setGlobalBusy(true);
    try {
      await reemplazarDocumento(item.adjunto_id, {
        solicitudId,
        documentoTipoId: docTipoId,
        archivo: file,
        fecha_emision: fecha || undefined,
      });
      resetFileInput();
      await onRefresh();
    } catch (e) {
      console.error(e);
      alert('No se pudo reemplazar el documento.');
    } finally {
      setLocalBusy(false); setGlobalBusy(false);
    }
  };

  const eliminar = async () => {
    if (!item.adjunto_id) return;
    if (!window.confirm(`¿Eliminar archivo de ${item.nombre}?`)) return;
    setLocalBusy(true); setGlobalBusy(true);
    try {
      await eliminarDocumento(item.adjunto_id);
      await onRefresh();
    } catch (e) {
      console.error(e);
      alert('No se pudo eliminar el documento.');
    } finally {
      setLocalBusy(false); setGlobalBusy(false);
    }
  };

  const archivoUrlAbs = item.archivo_url ? toAbsoluteUrl(item.archivo_url) : '';

  return (
    <div className="card">
      <div className="row">
        <div>
          <div className="title">
            {item.nombre} <span className="muted">({item.codigo})</span>
          </div>
          <div className="meta">
            {item.obligatorio ? 'Obligatorio' : 'Opcional'} · {recibido ? 'Recibido' : 'Faltante'}
            {observ && ` · ${item.motivo || 'Observado'}`}
          </div>
        </div>

        <div className={`badge ${recibido ? (observ ? 'warn' : 'ok') : ''}`}>
          {recibido ? (observ ? 'Observado' : 'OK') : 'Falta'}
        </div>
      </div>

      <div className="row" style={{ marginTop: 10 }}>
        <div className="inputs">
          <input
            key={fileKey}
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            disabled={disabled}
          />
          <input
            type="date"
            className="input"
            value={fecha || ''}
            onChange={(e) => setFecha(e.target.value)}
            disabled={disabled}
            title="Fecha de emisión del documento"
          />
        </div>

        <div className="actions">
          {archivoUrlAbs && (
            <a
              className="btn light"
              href={archivoUrlAbs}
              target="_blank"
              rel="noreferrer"
              download
            >
              Ver / Descargar
            </a>
          )}

          {!recibido ? (
            <button className="btn" onClick={subir} disabled={disabled || !file}>
              Subir
            </button>
          ) : (
            <>
              <button className="btn" onClick={reemplazar} disabled={disabled || !file}>
                Reemplazar
              </button>
              <button className="btn danger" onClick={eliminar} disabled={disabled}>
                Eliminar
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
