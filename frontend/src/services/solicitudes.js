import api from '../config/axios';

export async function listSolicitudes(params = {}) {
  const { data } = await api.get('/api/solicitudes/', { params });
  return data;
}

export async function createSolicitud(payload) {
  // payload: { cliente, monto, plazo_meses, tasa_nominal_anual, moneda }
  const { data } = await api.post('/api/solicitudes/', payload);
  return data;
}

export async function getSolicitud(id) {
  const { data } = await api.get(`/api/solicitudes/${id}/`);
  return data;
}

// src/services/solicitudes.js
export async function evaluarSolicitud(id, { score_riesgo, observacion_evaluacion }) {
  const { data } = await api.patch(`/api/solicitudes/${id}/evaluar/`, {
    score_riesgo,
    observacion_evaluacion,
  });
  return data;
}

export async function decidirSolicitud(id, decision /* 'APROBAR' | 'RECHAZAR' */) {
  const { data } = await api.post(`/api/solicitudes/${id}/decidir/`, { decision });
  return data;
}

export async function getChecklist(id) {
  const { data } = await api.get(`/api/solicitudes/${id}/documentos/checklist/`);
  return data;
}

export async function getSeguimiento(id) {
  const { data } = await api.get(`/api/solicitudes/${id}/seguimiento/`);
  return data;
}
