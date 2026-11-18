const AdminExaminers = {
  props: { limit: Number },
  emits: ['changed'],
  template: `
  <div>
    <div class="card shadow-sm mb-3">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span class="fw-bold text-danger">Examiners</span>
        <div>
          <router-link v-if="limit" to="/admin/examiners" class="btn btn-sm btn-link">View all</router-link>
          <button class="btn btn-sm btn-success" @click="openNew">+ New Examiner</button>
        </div>
      </div>
      <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
      <div v-if="notice" class="alert alert-warning m-2 py-2">{{ notice }}
        <button class="btn-close float-end" @click="notice = ''"></button></div>
      <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
      <div class="table-responsive">
        <table class="table table-sm table-hover mb-0 align-middle">
          <thead class="table-light"><tr>
            <th>Id</th><th>Name</th><th>Email</th><th>Contact details</th><th>Department</th><th>Status</th><th>Action</th>
          </tr></thead>
          <tbody>
            <tr v-for="x in shown" :key="x.id">
              <td>{{ x.id }}</td><td>{{ x.name }}</td><td>{{ x.email }}</td>
              <td>{{ x.contact_details }}</td><td>{{ x.department }}</td>
              <td><span :class="$badge(x.status)">{{ x.status }}</span></td>
              <td class="text-nowrap">
                <button class="btn btn-sm btn-outline-primary me-1" @click="openEdit(x)">View/Edit</button>
                <button v-if="x.status !== 'Approved'" class="btn btn-sm btn-outline-success me-1" @click="setStatus(x, 'Approved')">Approve</button>
                <button v-else class="btn btn-sm btn-outline-warning me-1" @click="setStatus(x, 'Deactivated')">Deactivate</button>
                <button class="btn btn-sm btn-outline-danger" @click="remove(x)">Remove</button>
              </td>
            </tr>
            <tr v-if="!shown.length"><td colspan="7" class="text-center text-muted">No examiners yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <modal-box :show="!!form" :title="form && form.id ? 'Edit Examiner' : 'New Examiner'" @close="form = null">
      <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
      <div v-if="form">
        <div class="mb-2"><label class="form-label mb-1">Name</label>
          <input v-model.trim="form.name" class="form-control"></div>
        <div class="mb-2"><label class="form-label mb-1">Email (login id)</label>
          <input v-model.trim="form.email" type="email" class="form-control" :disabled="!!form.id"></div>
        <div class="mb-2"><label class="form-label mb-1">Contact details</label>
          <input v-model.trim="form.contact_details" class="form-control"></div>
        <div class="mb-2"><label class="form-label mb-1">Department</label>
          <input v-model.trim="form.department" class="form-control"></div>
        <div class="mb-2"><label class="form-label mb-1 d-block">Status</label>
          <div class="form-check form-check-inline" v-for="s in ['Approved', 'Pending', 'Deactivated']" :key="s">
            <input class="form-check-input" type="radio" :id="'st' + s" :value="s" v-model="form.status">
            <label class="form-check-label" :for="'st' + s">{{ s }}</label>
          </div>
        </div>
        <div class="form-text">Login details are mailed to the examiner when the status becomes Approved.</div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="save">Update</button>
        <button class="btn btn-secondary" @click="form = null">Close</button>
      </template>
    </modal-box>
  </div>`,
  data() { return { examiners: [], form: null, formError: '', error: '', message: '', notice: '' }; },
  computed: {
    shown() { return this.limit ? this.examiners.slice(0, this.limit) : this.examiners; },
  },
  mounted() { this.load(); },
  methods: {
    async load() {
      try { this.examiners = await API.get('/admin/examiners'); }
      catch (e) { this.error = e.message; }
    },
    openNew() {
      this.formError = '';
      this.form = { id: null, name: '', email: '', contact_details: '', department: '', status: 'Approved' };
    },
    openEdit(x) { this.formError = ''; this.form = { ...x }; },
    showResult(res, who) {
      this.error = '';
      this.message = 'Examiner saved';
      const c = res.credentials;
      if (c && c.mail_sent) this.message = 'Login details mailed to ' + who;
      if (c && !c.mail_sent) this.notice = 'Mail is not configured. Temporary password for ' + who + ': ' + c.temp_password;
    },
    async save() {
      const f = this.form;
      try {
        const res = f.id ? await API.put('/admin/examiners/' + f.id, f) : await API.post('/admin/examiners', f);
        this.form = null;
        this.showResult(res, f.email);
        await this.load(); this.$emit('changed');
      } catch (e) { this.formError = e.message; }
    },
    async setStatus(x, status) {
      try {
        const res = await API.put('/admin/examiners/' + x.id, { ...x, status });
        this.showResult(res, x.email);
        await this.load();
      } catch (e) { this.message = ''; this.error = e.message; }
    },
    async remove(x) {
      if (!confirm('Remove examiner ' + x.name + '?')) return;
      try {
        await API.del('/admin/examiners/' + x.id);
        this.error = ''; this.message = 'Examiner removed';
        await this.load(); this.$emit('changed');
      } catch (e) { this.message = ''; this.error = e.message; }
    },
  },
};
