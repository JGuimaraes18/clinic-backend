import axios, { type AxiosRequestConfig } from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// =============================
// REQUEST INTERCEPTOR
// =============================
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// =============================
// REFRESH CONTROL
// =============================
let isRefreshing = false;
let failedQueue: {
  resolve: (token: string) => void;
  reject: (error: any) => void;
}[] = [];

function processQueue(error: any, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });

  failedQueue = [];
}

// =============================
// RESPONSE INTERCEPTOR
// =============================
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    if (!error.response) {
      return Promise.reject(error);
    }

    // Se não for 401 ou já tentou retry → rejeita
    if (error.response.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
      logoutAndRedirect();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return api(originalRequest);
      });
    }

    isRefreshing = true;

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/auth/token/refresh/`,
        { refresh: refreshToken }
      );

      const newAccessToken = response.data.access;

      localStorage.setItem("access_token", newAccessToken);

      api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;

      processQueue(null, newAccessToken);

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      }

      return api(originalRequest);
    } catch (err) {
      processQueue(err, null);
      logoutAndRedirect();
      return Promise.reject(err);
    } finally {
      isRefreshing = false;
    }
  }
);

// =============================
// LOGOUT GLOBAL
// =============================
function logoutAndRedirect() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");

  // Redireciona fora do React
  window.location.replace("/login");
}

export default api;