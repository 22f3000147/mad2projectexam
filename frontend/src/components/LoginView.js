const LoginView = {
  template: `
  <div class="container py-5" style="max-width:420px">
    <div class="card shadow-sm"><div class="card-body p-4">
      <h4 class="mb-3 text-center">Login</h4>
      <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
      <form @submit.prevent="submit" novalidate>
        <div class="mb-3">
          <label class="form-label">Email</label>
          <input v-model.trim="email" type="email" class="form-control" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input v-model="password" type="password" class="form-control" required>
        </div>
        <button class="btn btn-primary w-100" :disabled="loading">{{ loading ? 'Signing in...' : 'Login' }}</button>
      </form>
      <p class="small text-center mt-3 mb-0">New student? <router-link to="/register">Register</router-link></p>
    </div></div>
  </div>`,
  data() { return { email: '', password: '', error: '', loading: false }; },
  methods: {
    async submit() {
      this.error = '';
      if (!this.email || !this.password) { this.error = 'Email and password are required'; return; }
      this.loading = true;
      try {
        const res = await API.post('/auth/login', { email: this.email, password: this.password });
        authStore.setSession(res.token, res.user);
        this.$router.push(res.redirect);
      } catch (e) { this.error = e.message; }
      finally { this.loading = false; }
    },
  },
};
