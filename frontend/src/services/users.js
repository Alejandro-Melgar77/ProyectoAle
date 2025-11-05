import api from '../config/axios';

export async function getMe() {
  const { data } = await api.get('users/me/');
  return data;
}
