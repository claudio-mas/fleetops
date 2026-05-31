import axios, { type AxiosError } from "axios";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Endpoints onde um 401 é uma falha de credencial/TOTP esperada, tratada inline
// pelo componente — NÃO deslogar nem redirecionar para /login nesses casos.
const AUTH_ATTEMPT_PATHS = ["/auth/login", "/mfa/login"];

export function handleResponseError(err: AxiosError): Promise<never> {
  const url = err.config?.url ?? "";
  const isAuthAttempt = AUTH_ATTEMPT_PATHS.some((path) => url.includes(path));
  if (err.response?.status === 401 && !isAuthAttempt) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
  }
  return Promise.reject(err);
}

api.interceptors.response.use((res) => res, handleResponseError);
