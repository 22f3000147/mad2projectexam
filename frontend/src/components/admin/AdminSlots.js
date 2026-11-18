
const AdminSlots = {
  template: `
  <div class="card shadow-sm">
    <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
      <span class="fw-bold text-danger">Examination Slots</span>
      <div class="d-flex gap-2">
        <select v-model="examFilter" class="form-select form-select-sm" @change="load">
          <option value="">All exams</option>
          <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.id }} - {{ e.name }}</option>
        </select>
        <button class="btn btn-sm btn-success text-nowrap" @click="openNew">+ Slots</button>
      </div>
    </div>
    <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Id</th><th>Exam</th><th>Examiner</th><th>Date</th><th>Time</th><th>Seats</th><th>Status</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="s in slots" :key="s.id">
            <td>{{ s.id }}</td><td>{{ s.course_code }} - {{ s.exam_name }}</td><td>{{ s.examiner_name }}</td>
            <td>{{ s.date }}</td><td>{{ s.start_time }} - {{ s.end_time }}</td>
            <td>{{ s.available_seats }} / {{ s.max_capacity }}</td>
            <td><span :class="$badge(s.status)">{{ s.status }}</span></td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-outline-primary me-1" @click="openEdit(s)">Edit</button>
              <button class="btn btn-sm btn-outline-danger" @click="remove(s)">Delete</button>
            </td>
          </tr>
          <tr v-if="!slots.length"><td colspan="8" class="text-center text-muted">No slots yet</td></tr>
        </tbody>
      </table>
    </div>

    <modal-box :show="!!form" :title="form && form.id ? 'Edit Slot' : 'Create Slot'" @close="form = null">
      <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
      <div v-if="form" class="row g-2">
        <div class="col-12"><label class="form-label mb-1">Exam Id</label>
          <select v-model="form.examination_id" class="form-select" :disabled="!!form.id" @change="form.examiner_id = ''">
            <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.id }} - {{ e.name }}</option>
          </select></div>
        <div class="col-12"><label class="form-label mb-1">Examiner</label>
          <select v-model="form.examiner_id" class="form-select">
            <option value="" disabled>Select examiner</option>
            <option v-for="x in formExaminers" :key="x.id" :value="x.id">{{ x.name }}</option>
          </select>
          <div v-if="!formExaminers.length" class="form-text text-danger">Assign examiners to this exam first.</div></div>
        <div class="col-12"><label class="form-label mb-1">Date</label>
          <input v-model="form.date" type="date" class="form-control"></div>
        <div class="col-6"><label class="form-label mb-1">Start time</label>
          <input v-model="form.start_time" type="time" class="form-control"></div>
        <div class="col-6"><label class="form-label mb-1">End time</label>
          <input v-model="form.end_time" type="time" class="form-control"></div>
        <div class="col-6"><label class="form-label mb-1">Max capacity</label>
          <input v-model.number="form.max_capacity" type="number" min="1" class="form-control"></div>
        <div class="col-6"><label class="form-label mb-1">Status</label>
          <select v-model="form.status" class="form-select"><option>Available</option><option>Cancelled</option></select></div>
        <div class="col-12"><label class="form-label mb-1">Meeting link (optional)</label>
          <input v-model.trim="form.meeting_link" class="form-control"></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="save">Update</button>
        <button class="btn btn-secondary" @click="form = null">Cancel</button>
      </template>
    </modal-box>
  </div>`,
  data() {
    return { slots: [], exams: [], examFilter: this.$route.query.exam ? Number(this.$route.query.exam) : '',
             form: null, formError: '', error: '', message: '' };
  },
  computed: {
    formExaminers() {
      const e = this.form && this.exams.find(x => x.id === this.form.examination_id);
      return e ? e.examiners : [];
    },
  },
  async mounted() {
    try { this.exams = await API.get('/admin/exams'); } catch (e) { this.error = e.message; }
    this.load();
  },
  methods: {
    async load() {
      try {
        this.slots = await API.get('/admin/slots' + (this.examFilter ? '?exam_id=' + this.examFilter : ''));
        this.exams = await API.get('/admin/exams');
      } catch (e) { this.error = e.message; }
    },
    openNew() {
      this.formError = '';
      this.form = { id: null, examination_id: this.examFilter || (this.exams.length ? this.exams[0].id : ''),
        examiner_id: '', date: '', start_time: '', end_time: '', max_capacity: 10, status: 'Available', meeting_link: '' };
    },
    openEdit(s) { this.formError = ''; this.form = { ...s, status: s.status === 'Cancelled' ? 'Cancelled' : 'Available' }; },
    async save() {
      const f = this.form;
      try {
        if (f.id) await API.put('/admin/slots/' + f.id, f);
        else await API.post('/admin/slots', f);
        this.form = null; this.error = ''; this.message = 'Slot saved';
        await this.load();
      } catch (e) { this.formError = e.message; }
    },
    async remove(s) {
      if (!confirm('Delete slot ' + s.id + '?')) return;
      try { await API.del('/admin/slots/' + s.id); this.error = ''; this.message = 'Slot deleted'; await this.load(); }
      catch (e) { this.message = ''; this.error = e.message; }
    },
  },
};
