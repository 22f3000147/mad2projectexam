const AdminStudents = {
  template: `
  <div class="card shadow-sm">
    <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
      <span class="fw-bold text-danger">Students</span>
      <form class="d-flex" @submit.prevent="load">
        <input v-model.trim="q" class="form-control form-control-sm" placeholder="Name, email or Id">
        <button class="btn btn-sm btn-primary ms-2">Search</button>
      </form>
    </div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr><th>Id</th><th>Name</th><th>Email</th><th>Phone</th><th>Department</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>
          <tr v-for="s in students" :key="s.id">
            <td>{{ s.id }}</td><td>{{ s.name }}</td><td>{{ s.email }}</td><td>{{ s.phone }}</td><td>{{ s.department }}</td>
            <td><span :class="$badge(s.is_active ? 'Active' : 'Inactive')">{{ s.is_active ? 'Active' : 'Inactive' }}</span></td>
            <td><button class="btn btn-sm" :class="s.is_active ? 'btn-outline-warning' : 'btn-outline-success'" @click="toggle(s)">
              {{ s.is_active ? 'Deactivate' : 'Activate' }}</button></td>
          </tr>
          <tr v-if="!students.length"><td colspan="7" class="text-center text-muted">No students found</td></tr>
        </tbody>
      </table>
    </div>
  </div>`,
  data() { return { students: [], q: '', error: '' }; },
  mounted() { this.load(); },
  methods: {
    async load() {
      try { this.students = await API.get('/admin/students?q=' + encodeURIComponent(this.q)); this.error = ''; }
      catch (e) { this.error = e.message; }
    },
    async toggle(s) {
      try { await API.put('/admin/students/' + s.id + '/active', { is_active: !s.is_active }); await this.load(); }
      catch (e) { this.error = e.message; }
    },
  },
};
