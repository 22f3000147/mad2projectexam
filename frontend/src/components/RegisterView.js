const RegisterView = {
  template: `
  <div class="container py-5" style="max-width:480px">
    <div class="card shadow-sm"><div class="card-body p-4">
      <h4 class="mb-3 text-center">Student Registration</h4>
      <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
      <div v-if="success" class="alert alert-success py-2">{{ success }}</div>
      <form @submit.prevent="submit" novalidate>
        <div class="mb-2" v-for="f in fields" :key="f.key">
          <label class="form-label mb-1">{{ f.label }}</label>
          <input v-model.trim="form[f.key]" :type="f.type" class="form-control"
                 :class="{'is-invalid': errors[f.key]}">
          <div class="invalid-feedback">{{ errors[f.key] }}</div>
        </div>
        <div class="mb-3"><label class="form-label mb-1">User type</label>
          <input class="form-control" value="Student" disabled></div>
        <button class="btn btn-primary w-100" :disabled="loading">Sign up</button>
      </form>
      <p class="small text-center mt-3 mb-0">Existing user? <router-link to="/login">Login</router-link></p>
    </div></div>
  </div>`,
  data() {
    return {
      form: { email: '', password: '', full_name: '', phone: '', department: '' },
      fields: [
        { key: 'email', label: 'Email (username)', type: 'email' },
        { key: 'password', label: 'Password', type: 'password' },
        { key: 'full_name', label: 'Full name', type: 'text' },
        { key: 'phone', label: 'Phone no. (10 digits)', type: 'tel' },
        { key: 'department', label: 'Department', type: 'text' },
      ],
      errors: {}, error: '', success: '', loading: false,
    };
  },
  methods: {
    validate() {
      const e = {};
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(this.form.email)) e.email = 'Valid email required';
      if (this.form.password.length < 6) e.password = 'Min 6 characters';
      if (!this.form.full_name) e.full_name = 'Full name required';
      if (this.form.phone && !/^\d{10}$/.test(this.form.phone)) e.phone = 'Phone must be 10 digits';
      this.errors = e;
      return !Object.keys(e).length;
    },
    async submit() {
      this.error = ''; this.success = '';
      if (!this.validate()) return;
      this.loading = true;
      try {
        const res = await API.post('/auth/register', this.form);
        this.success = res.message;
        setTimeout(() => this.$router.push('/login'), 1200);
      } catch (e) { this.errors = e.fields || {}; this.error = e.message; }
      finally { this.loading = false; }
    },
  },
};
