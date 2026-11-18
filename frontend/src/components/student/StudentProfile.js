const StudentProfile = {
  template: `
  <div class="card shadow-sm mx-auto" style="max-width:520px">
    <div class="card-header fw-bold text-danger">My Profile</div>
    <div class="card-body">
      <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
      <div v-if="message" class="alert alert-success py-2">{{ message }}</div>
      <form v-if="form" @submit.prevent="save" novalidate>
        <div class="mb-2"><label class="form-label mb-1">Email (cannot change)</label>
          <input :value="form.email" class="form-control" disabled></div>
        <div class="mb-2"><label class="form-label mb-1">Full name</label>
          <input v-model.trim="form.full_name" class="form-control"></div>
        <div class="mb-2"><label class="form-label mb-1">Phone no. (10 digits)</label>
          <input v-model.trim="form.phone" class="form-control"></div>
        <div class="mb-3"><label class="form-label mb-1">Department</label>
          <input v-model.trim="form.department" class="form-control"></div>
        <div class="fw-bold mb-1">Change password (optional)</div>
        <div class="row g-2 mb-3">
          <div class="col"><input v-model="form.current_password" type="password" class="form-control" placeholder="Current password"></div>
          <div class="col"><input v-model="form.new_password" type="password" class="form-control" placeholder="New password"></div>
        </div>
        <button class="btn btn-primary">Update</button>
      </form>
    </div>
  </div>`,
  data() { return { form: null, error: '', message: '' }; },
  async mounted() {
    try { this.form = { ...(await API.get('/student/profile')), current_password: '', new_password: '' }; }
    catch (e) { this.error = e.message; }
  },
  methods: {
    async save() {
      this.error = ''; this.message = '';
      if (!this.form.full_name) { this.error = 'Full name is required'; return; }
      if (this.form.phone && !/^\d{10}$/.test(this.form.phone)) { this.error = 'Phone must be 10 digits'; return; }
      try {
        const user = await API.put('/student/profile', this.form);
        authStore.setSession(authStore.token, user);          // navbar shows the new name
        this.form.current_password = ''; this.form.new_password = '';
        this.message = 'Profile updated';
      } catch (e) { this.error = e.message; }
    },
  },
};
