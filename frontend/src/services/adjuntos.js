import api from '../config/axios';

export function listAdjuntos({ solicitud }) {
  return api.get('/api/documentos/', { params: { solicitud } })
           .then(r => r.data);
}

export function subirAdjunto({ solicitud, documento_tipo, archivo, fecha_emision }) {
  const fd = new FormData();
  fd.append('solicitud', solicitud);
  fd.append('documento_tipo', documento_tipo);
  fd.append('archivo', archivo);
  if (fecha_emision) fd.append('fecha_emision', fecha_emision);
  return api.post('/api/documentos/', fd, { headers: { 'Content-Type':'multipart/form-data' } })
           .then(r => r.data);
}

export function reemplazarAdjunto(id, { solicitud, documento_tipo, archivo, fecha_emision }) {
  const fd = new FormData();
  if (solicitud) fd.append('solicitud', solicitud);
  if (documento_tipo) fd.append('documento_tipo', documento_tipo);
  if (archivo) fd.append('archivo', archivo);
  if (fecha_emision) fd.append('fecha_emision', fecha_emision);
  // PATCH para no exigir todos los campos
  return api.patch(`/api/documentos/${id}/`, fd, { headers: { 'Content-Type':'multipart/form-data' } })
           .then(r => r.data);
}

export function eliminarAdjunto(id) {
  return api.delete(`/api/documentos/${id}/`).then(() => true);
}
