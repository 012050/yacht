import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
});

// Normalize backend status ("playing"/"finished"/"waiting") to uppercase.
api.interceptors.response.use((response) => {
  const body = response.data;
  if (body && typeof body === 'object') {
    if (typeof body.status === 'string') {
      body.status = body.status.toUpperCase();
    }
    if (Array.isArray(body) && body.length > 0 && body[0]?.status) {
      body.forEach((item: { status?: string }) => {
        if (typeof item.status === 'string') {
          item.status = item.status.toUpperCase();
        }
      });
    }
  }
  return response;
});

export default api;
