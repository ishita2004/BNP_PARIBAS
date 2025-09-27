import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export const uploadFiles = (formData) => {
  return axios.post(`${API_URL}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const askQuery = (query) => {
  return axios.post(`${API_URL}/ask`, { query });
};
