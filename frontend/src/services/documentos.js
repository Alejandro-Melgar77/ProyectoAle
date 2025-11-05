// src/services/documentos.js
import api from '../config/axios';

/** GET /api/documento-tipos/ */
export async function listDocumentoTipos() {
  const { data } = await api.get('/api/documento-tipos/');
  return data;
}

/** POST /api/documentos/  (multipart)  -> crear adjunto */
export async function subirDocumento({ solicitudId, documentoTipoId, archivo, fecha_emision }) {
  const fd = new FormData();
  fd.append('solicitud', solicitudId);
  fd.append('documento_tipo', documentoTipoId);
  if (fecha_emision) fd.append('fecha_emision', fecha_emision);
  if (archivo) fd.append('archivo', archivo);

  const { data } = await api.post('/api/documentos/', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

/** PATCH /api/documentos/:id/  (multipart) -> reemplazar archivo / fecha */
export async function reemplazarDocumento(adjuntoId, { solicitudId, documentoTipoId, archivo, fecha_emision }) {
  const fd = new FormData();
  // Solo envía lo que quieras modificar:
  if (solicitudId) fd.append('solicitud', solicitudId);
  if (documentoTipoId) fd.append('documento_tipo', documentoTipoId);
  if (fecha_emision) fd.append('fecha_emision', fecha_emision);
  if (archivo) fd.append('archivo', archivo);

  const { data } = await api.patch(`/api/documentos/${adjuntoId}/`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

/** DELETE /api/documentos/:id/ -> eliminar adjunto */
export async function eliminarDocumento(adjuntoId) {
  await api.delete(`/api/documentos/${adjuntoId}/`);
  return true;
}
