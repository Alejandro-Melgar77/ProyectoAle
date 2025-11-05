// src/services/simulador.js
import api from '../config/axios';

export async function simular({ monto, plazo_meses, tasa_nominal_anual, primera_cuota_fecha }) {
  const { data } = await api.post('/api/simulador/', {
    monto, plazo_meses, tasa_nominal_anual, primera_cuota_fecha
  });
  return data; // { resumen, cuotas }
}
