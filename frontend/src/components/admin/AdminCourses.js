const AdminCourses = {
  props: { limit: Number },          
  emits: ['changed'],
  template: `
  <div>
    <div class="card shadow-sm mb-3">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span class="fw-bold text-danger">Courses</span>
        <div>
          <router-link v-if="limit" to="/admin/courses" class="btn btn-sm btn-link">View all</router-link>
          <button class="btn btn-sm btn-success" @click="openNew">+ New Course</button>
        </div>
      </div>
      <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
      <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
      <div class="table-responsive">
        <table class="table table-sm table-hover mb-0 align-middle">
          <thead class="table-light"><tr>
            <th>Id</th><th>Course code</th><th>Name</th><th>Description</th><th>Status</th><th>Action</th>
          </tr></thead>
          <tbody>
            <tr v-for="c in shown" :key="c.id">
              <td>{{ c.id }}</td><td>{{ c.code }}</td><td>{{ c.name }}</td>
              <td class="text-truncate" style="max-width:260px">{{ c.description }}</td>
              <td><span :class="$badge(c.status)">{{ c.status }}</span></td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-1" @click="openEdit(c)">Edit</button>
                <button class="btn btn-sm btn-outline-danger" @click="remove(c)">Delete</button>
              </td>
            </tr>
            <tr v-if="!shown.length"><td colspan="6" class="text-center text-muted">No courses yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <modal-box :show="!!form" :title="form && form.id ? 'Edit Course' : 'New Course'" @close="form = null">
      <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
      <div v-if="form">
        <div class="mb-2"><label class="form-label mb-1">Course code</label>
          <input v-model.trim="form.code" class="form-control"></div>
        <div class="mb-2"><label class="form-label mb-1">Name</label>
          <input v-model.trim="form.name" class="form-control"></div>
        <div class="mb-2"><label class="form-label mb-1">Description</label>
          <textarea v-model="form.description" rows="3" class="form-control"></textarea></div>
        <div class="form-check">
          <input class="form-check-input" type="checkbox" id="courseActive" v-model="form.active">
          <label class="form-check-label" for="courseActive">Active</label>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="save">Update</button>
        <button class="btn btn-secondary" @click="form = null">Cancel</button>
      </template>
    </modal-box>
  </div>`,
  data() { return { courses: [], form: null, formError: '', error: '', message: '' }; },
  computed: {
    shown() { return this.limit ? this.courses.slice(0, this.limit) : this.courses; },
  },
  mounted() { this.load(); },
  methods: {
    async load() {
      try { this.courses = await API.get('/admin/courses'); }
      catch (e) { this.error = e.message; }
    },
    openNew() { this.formError = ''; this.form = { id: null, code: '', name: '', description: '', active: true }; },
    openEdit(c) { this.formError = ''; this.form = { ...c, active: c.status === 'Active' }; },
    async save() {
      const f = this.form;
      const payload = { code: f.code, name: f.name, description: f.description, status: f.active ? 'Active' : 'Inactive' };
      try {
        if (f.id) await API.put('/admin/courses/' + f.id, payload);
        else await API.post('/admin/courses', payload);
        this.form = null; this.error = '';
        this.message = 'Course saved';
        await this.load(); this.$emit('changed');
      } catch (e) { this.formError = e.message; }
    },
    async remove(c) {
      if (!confirm('Delete course ' + c.code + ' and all its exams?')) return;
      try {
        await API.del('/admin/courses/' + c.id);
        this.error = ''; this.message = 'Course deleted';
        await this.load(); this.$emit('changed');
      } catch (e) { this.message = ''; this.error = e.message; }
    },
  },
};
