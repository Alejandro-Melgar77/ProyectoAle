import React, { useState } from 'react';
import axios from '../../config/axios';

export default function SolicitudForm({ onCreated }) {
  const [form, setForm] = useState({ cliente:'', monto:'', plazo_meses:'', tasa_nominal_anual:'', moneda:'BOB' });
  const [err, setErr] = useState('');
  const submit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/solicitudes/', form, { withCredentials:true });
      setErr(''); onCreated && onCreated();
    } catch (e) { setErr(e?.response?.data?.detail || 'Error'); }
  };
  return (
    <form onSubmit={submit} className="space-y-2">
      <input placeholder="ID Cliente" value={form.cliente} onChange={e=>setForm({...form,cliente:e.target.value})}/>
      <input placeholder="Monto" type="number" value={form.monto} onChange={e=>setForm({...form,monto:e.target.value})}/>
      <input placeholder="Plazo (meses)" type="number" value={form.plazo_meses} onChange={e=>setForm({...form,plazo_meses:e.target.value})}/>
      <input placeholder="Tasa anual (%)" type="number" step="0.0001" value={form.tasa_nominal_anual} onChange={e=>setForm({...form,tasa_nominal_anual:e.target.value})}/>
      <button type="submit">Crear solicitud</button>
      {err && <div className="text-red-600 text-sm">{err}</div>}
    </form>
  );
}
