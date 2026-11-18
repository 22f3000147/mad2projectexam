
const authStore = Vue.reactive({
  token: localStorage.getItem('emp_token'),
  user: JSON.parse(localStorage.getItem('emp_user') || 'null'),

  get isLoggedIn() { return !!this.token && !!this.user; },
  get role() { return this.user ? this.user.role : null; },

  setSession(token, user) {
    this.token = token; this.user = user;
    localStorage.setItem('emp_token', token);
    localStorage.setItem('emp_user', JSON.stringify(user));
  },
  clear() {
    this.token = null; this.user = null;
    localStorage.removeItem('emp_token');
    localStorage.removeItem('emp_user');
  },
});
