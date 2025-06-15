import axios from 'axios';

const api = axios.create({
  baseURL: 'https://ares-api-dev-avetckd5ecdgbred.canadacentral-01.azurewebsites.net',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

export default api;
