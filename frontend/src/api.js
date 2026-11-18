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

  async blob(path) {
    const res = await fetch('/api' + path, { headers: { Authorization: 'Bearer ' + localStorage.getItem('emp_token') } });
    if (!res.ok) throw new Error('Could not load the file');
    return res.blob();
  },
  async download(path, filename) {
    const url = URL.createObjectURL(await API.blob(path));
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  },
  async openTab(path) { window.open(URL.createObjectURL(await API.blob(path)), '_blank'); },
  wait: (ms) => new Promise(r => setTimeout(r, ms)),
};
