import axios from 'axios';

const api = axios.create({
  baseURL: 'https://<YOUR-BACKEND-URL>.azurewebsites.net', // Replace with your backend URL
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
