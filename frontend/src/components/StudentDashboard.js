const StudentDashboard = {
  template: `
  <div class="container py-4">
    <h3>Student Dashboard</h3>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-else class="alert alert-success">{{ message || 'Loading...' }}</div>
    <p class="text-muted">Features arrive in upcoming milestones.</p>
  </div>`,
  data() { return { message: '', error: '' }; },
  async mounted() {
    try { this.message = (await API.get('/student/dashboard')).message; }
    catch (e) { this.error = e.message; }
  },
};
