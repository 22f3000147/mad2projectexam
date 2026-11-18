const ExaminerSlots = {
  template: `
  <div class="card shadow-sm">
    <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
      <span class="fw-bold text-danger">My Slots</span>
      <div class="d-flex gap-2">
        <select v-model="examFilter" class="form-select form-select-sm" @change="load">
          <option value="">All exams</option>
          <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.id }} - {{ e.name }}</option>
        </select>
        <button class="btn btn-sm btn-success text-nowrap" :disabled="!creatable.length" @click="openNew">+ New Slot</button>
      </div>
    </div>
    <div v-if="!creatable.length" class="small text-muted px-3 pt-2">Slot creation is not open for any of your exams right now.</div>
    <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Id</th><th>Exam</th><th>Date</th><th>Time</th><th>Booked</th><th>Status</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="s in slots" :key="s.id">
            <td>{{ s.id }}</td><td>{{ s.course_code }} - {{ s.exam_name }}</td><td>{{ s.date }}</td>
            <td>{{ s.start_time }} - {{ s.end_time }}</td><td>{{ s.booked }} / {{ s.max_capacity }}</td>
            <td><span :class="$badge(s.status)">{{ s.status }}</span></td>
            <td class="text-nowrap">
              <template v-if="s.can_edit">
                <button class="btn btn-sm btn-outline-primary me-1" @click="openEdit(s)">Edit</button>
                <button class="btn btn-sm btn-outline-danger" @click="remove(s)">Remove</button>
              </template>
              <span v-else class="small text-muted">{{ s.lock_reason }}</span>
            </td>
          </tr>
          <tr v-if="!slots.length"><td colspan="7" class="text-center text-muted">You have not created any slots</td></tr>
        </tbody>
      </table>
    </div>

    <modal-box :show="!!form" :title="form && form.id ? 'Edit Slot' : 'Create Slot'" @close="form = null">
      <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
      <div v-if="form" class="row g-2">
        <div class="col-12"><label class="form-label mb-1">Exam Id</label>
          <select v-model="form.examination_id" class="form-select" :disabled="!!form.id">
            <option v-for="e in (form.id ? exams : creatable)" :key="e.id" :value="e.id">{{ e.id }} - {{ e.name }}</option>
          </select></div>
        <div class="col-12"><label class="form-label mb-1">Date</label>
          <input v-model="form.date" type="date" class="form-control"></div>
        <div class="col-6"><label class="form-label mb-1">Start time</label>
          <input v-model="form.start_time" type="time" class="form-control"></div>
        <div class="col-6"><label class="form-label mb-1">End time</label>
          <input v-model="form.end_time" type="time" class="form-control"></div>
        <div class="col-12"><label class="form-label mb-1">Max capacity</label>
          <input v-model.number="form.max_capacity" type="number" min="1" class="form-control"></div>
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
  computed: { creatable() { return this.exams.filter(e => e.can_create_slots); } },
  async mounted() {
    await this.load();
    if (this.$route.query.new && this.creatable.length) this.openNew();   // came from "+ Fill availability"
  },
  methods: {
    async load() {
      try {
        this.exams = await API.get('/examiner/exams');
        this.slots = await API.get('/examiner/slots' + (this.examFilter ? '?exam_id=' + this.examFilter : ''));
      } catch (e) { this.error = e.message; }
    },
    openNew() {
      this.formError = '';
      const pick = this.creatable.find(e => e.id === this.examFilter) || this.creatable[0];
      this.form = { id: null, examination_id: pick.id, date: '', start_time: '', end_time: '', max_capacity: 5, meeting_link: '' };
    },
    openEdit(s) { this.formError = ''; this.form = { ...s }; },
    async save() {
      const f = this.form;
      try {
        if (f.id) await API.put('/examiner/slots/' + f.id, f);
        else await API.post('/examiner/slots', f);
        this.form = null; this.error = ''; this.message = 'Slot saved';
        await this.load();
      } catch (e) { this.formError = e.message; }
    },
    async remove(s) {
      if (!confirm('Remove slot ' + s.id + '?')) return;
      try { await API.del('/examiner/slots/' + s.id); this.error = ''; this.message = 'Slot removed'; await this.load(); }
      catch (e) { this.message = ''; this.error = e.message; }
    },
  },
};
