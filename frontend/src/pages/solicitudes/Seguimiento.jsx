import React, { useEffect, useState } from 'react';
import { getSeguimiento } from '../../services/solicitudes';
import { useParams } from 'react-router-dom';

export default function Seguimiento(){
  const { id } = useParams();
  const [data, setData] = useState(null);

  useEffect(()=>{
    (async()=>{
      const res = await getSeguimiento(id);
      setData(res);
    })();
  },[id]);

  if (!data) return <div>Cargando…</div>;

  return (
    <div style={{maxWidth:700}}>
      <h2>Seguimiento — Solicitud {id}</h2>
      <div className="badge">Estado actual: <b>{data.estadoActual}</b></div>
      <ul className="time">
        {data.timelineEstados?.map((t,i)=>(
          <li key={i}>
            <span className="dot">●</span>
            <div className="evt">{t.evento}</div>
            <div className="ts">{new Date(t.fecha).toLocaleString()}</div>
          </li>
        ))}
      </ul>
      <style>{`
        .badge { background:#eef2ff; color:#3730a3; display:inline-block; padding:6px 10px; border-radius:999px; margin:8px 0; }
        .time { list-style:none; padding:0; margin:12px 0; display:grid; gap:6px; }
        .time li { display:grid; grid-template-columns: 24px 1fr auto; align-items:center; background:#fff; border-radius:8px; padding:8px; }
        .dot { color:#1d4ed8; }
        .evt { font-weight:600; }
        .ts { color:#64748b; font-size:.9rem; }
      `}</style>
    </div>
  );
}
