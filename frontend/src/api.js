
const API = {
  async request(path, { method = 'GET', body } = {}) {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('emp_token');
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const res = await fetch('/api' + path, {
      method, headers, body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error(data.error || data.msg || 'Request failed');
      err.status = res.status; err.fields = data.fields || {};
      throw err;
    }
    return data;
  },
  get: (p) => API.request(p),
  post: (p, body) => API.request(p, { method: 'POST', body }),
  put: (p, body) => API.request(p, { method: 'PUT', body }),
  del: (p) => API.request(p, { method: 'DELETE' }),
};
