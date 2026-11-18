const NavBar = {
  template: `
  <nav class="navbar navbar-dark bg-primary px-3">
    <span class="navbar-brand mb-0 h1">Examination Management Portal</span>
    <div v-if="auth.isLoggedIn" class="d-flex align-items-center gap-3 text-white">
      <span class="small">{{ auth.user.full_name }} <span class="badge bg-light text-primary text-uppercase">{{ auth.role }}</span></span>
      <button class="btn btn-sm btn-outline-light" @click="logout">Logout</button>
    </div>
  </nav>`,
  data() { return { auth: authStore }; },
  methods: {
    logout() { authStore.clear(); this.$router.push('/login'); },
  },
};
