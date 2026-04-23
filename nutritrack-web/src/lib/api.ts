import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 30_000,
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("nutritrack_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("nutritrack_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;

// ── Typed API helpers ─────────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, password: string, fullName?: string) =>
    api.post("/auth/register", { email, password, full_name: fullName }),
  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    return api.post<{ access_token: string }>("/auth/token", form);
  },
  me: () => api.get("/auth/me"),
};

export const predictApi = {
  predict: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/predict/", form);
  },
  history: () => api.get("/predict/history"),
};

export const ingredientsApi = {
  get: (foodName: string) => api.get(`/ingredients/${encodeURIComponent(foodName)}`),
};

export const shoppingApi = {
  getLists:    ()               => api.get("/shopping/"),
  createList:  (name: string)   => api.post("/shopping/", { name }),
  deleteList:  (id: number)     => api.delete(`/shopping/${id}`),
  addItem:     (listId: number, item: object) => api.post(`/shopping/${listId}/items`, item),
  addBulk:     (listId: number, items: object[]) => api.post(`/shopping/${listId}/items/bulk`, items),
  updateItem:  (listId: number, itemId: number, patch: object) =>
                 api.patch(`/shopping/${listId}/items/${itemId}`, patch),
  deleteItem:  (listId: number, itemId: number) =>
                 api.delete(`/shopping/${listId}/items/${itemId}`),
};

export const spendingApi = {
  getLogs:     ()              => api.get("/spending/"),
  logSpending: (payload: object) => api.post("/spending/", payload),
  summary:     ()              => api.get("/spending/summary"),
};
