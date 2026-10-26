import axios from "axios";
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
});
let token = sessionStorage.getItem("argus-token");
export const getToken = () => token;
export function setToken(value) {
  token = value;
  if (value) sessionStorage.setItem("argus-token", value);
  else sessionStorage.removeItem("argus-token");
}
api.interceptors.request.use((config) => {
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(
  (value) => value,
  (error) => {
    if (
      error.response?.status === 401 &&
      !error.config.url.includes("/auth/login")
    ) {
      setToken(null);
      window.location.assign("/login");
    }
    return Promise.reject(error);
  },
);
export const message = (error) =>
  error.response?.data?.error || error.message || "Request failed";
