import api from '../config/axios';

// Lista requisitos filtrando por producto y tipo trabajador
export async function listRequisitos({ producto, tipo_trabajador }) {
  const { data } = await api.get('/api/requisitos/', {
    params: { producto, tipo_trabajador }
  });
  return data; // [{id, producto, tipo_trabajador, documento:{...}, obligatorio}, ...]
}

export async function createRequisito(payload) {
  // payload: { producto, tipo_trabajador, documento, obligatorio }
  const { data } = await api.post('/api/requisitos/', payload);
  return data;
}

export async function updateRequisito(id, payload) {
  const { data } = await api.patch(`/api/requisitos/${id}/`, payload);
  return data;
}

export async function deleteRequisito(id) {
  await api.delete(`/api/requisitos/${id}/`);
}
