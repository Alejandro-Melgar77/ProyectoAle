import api from '../config/axios';

// Puedes usar /api/clientes/ (devuelve los Cliente con su id)
export async function fetchClientes() {
  const { data } = await api.get('/api/clientes/');
  return data; // array de clientes
}
