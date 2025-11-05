// Convierte /media/... o media/... en URL absoluta usando el baseURL de axios
import api from '../config/axios';

export function toAbsoluteUrl(pathOrUrl) {
  if (!pathOrUrl) return '';
  try {
    // si ya es absoluta (http/https), devuélvela tal cual
    const u = new URL(pathOrUrl);
    if (u.protocol === 'http:' || u.protocol === 'https:') return pathOrUrl;
  } catch {
    // no era absoluta → seguimos
  }

  // normaliza: evita dobles slashes
  const base = (api.defaults.baseURL || '').replace(/\/+$/, '');
  const path = String(pathOrUrl).replace(/^\/+/, '');
  return `${base}/${path}`;
}
