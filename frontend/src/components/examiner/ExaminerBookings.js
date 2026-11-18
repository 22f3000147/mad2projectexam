const ExaminerBookings = {
  props: { limit: Number },
  emits: ['changed'],
  template: `
  <div class="card shadow-sm mb-3">
    <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
      <span class="fw-bold text-danger">Booked Slots</span>
      <router-link v-if="limit" to="/examiner/bookings" class="btn btn-sm btn-link">View all</router-link>
      <form v-else class="d-flex gap-2" @submit.prevent="load">
        <select v-model="examId" class="form-select form-select-sm">
          <option value="">All exams</option>
          <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.id }} - {{ e.name }}</option>
        </select>
        <input v-model.trim="q" class="form-control form-control-sm" placeholder="Student Id / name">
        <button class="btn btn-sm btn-primary">Search</button>
      </form>
    </div>
    <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Booking Id</th><th>Slot Id</th><th>Student</th><th>Exam</th><th>Date / time</th>
          <th>Booking</th><th>Evaluation</th><th>Marks</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="b in shown" :key="b.id">
            <td>{{ b.id }}</td><td>{{ b.slot_id }}</td><td>{{ b.student_id }} - {{ b.student_name }}</td>
            <td>{{ b.course_code }} {{ b.exam_name }}</td>
            <td>{{ b.slot_date }} {{ b.slot_start }}-{{ b.slot_end }}</td>
            <td><span :class="$badge(b.status)">{{ b.status }}</span></td>
            <td><span :class="evalBadge(b.eval_status)">{{ b.eval_status }}</span></td>
            <td>{{ b.marks === null ? '-' : b.marks }}</td>
            <td><button class="btn btn-sm btn-success" @click="openEval(b)">+Rubrics</button></td>
          </tr>
          <tr v-if="!shown.length"><td colspan="9" class="text-center text-muted">No students booked in your slots yet</td></tr>
        </tbody>
      </table>
    </div>

    <modal-box :show="!!ev" title="Rubrics" size="modal-lg" @close="ev = null">
      <div v-if="evError" class="alert alert-danger py-2">{{ evError }}</div>
      <div v-if="ev">
        <div class="row mb-2 small">
          <div class="col-md-3"><b>Slot Id:</b> {{ ev.booking.slot_id }}</div>
          <div class="col-md-4"><b>Student Id:</b> {{ ev.booking.student_id }} ({{ ev.booking.student_name }})</div>
          <div class="col-md-5"><b>Examination date/time:</b> {{ ev.booking.slot_date }} {{ ev.booking.slot_start }}</div>
        </div>
        <div v-if="ev.locked" class="alert alert-secondary py-2">Evaluation is locked (results published or exam not in evaluation stage).</div>
        <div v-if="!ev.rubrics.length" class="alert alert-warning py-2">Admin has not added rubric criteria for this exam yet.</div>
        <div class="row g-2 align-items-center mb-2" v-for="(r, i) in ev.rubrics" :key="r.id">
          <div class="col-md-7">Criteria {{ i + 1 }}: <b>{{ r.criterion_name }}</b>
            <div class="small text-muted">{{ r.description }}</div></div>
          <div class="col-md-5 d-flex align-items-center gap-2">
            <span class="small text-nowrap">Awarded marks</span>
            <input v-model.number="r.awarded" type="number" min="0" :max="r.max_marks" step="0.5"
                   class="form-control form-control-sm" :disabled="ev.locked">
            <span class="small text-nowrap">/ {{ r.max_marks }}</span>
          </div>
        </div>
        <div class="fw-bold mb-2">Total: {{ total }} / {{ ev.exam_max }}</div>
        <label class="form-label mb-1">Remarks</label>
        <textarea v-model="ev.remarks" rows="2" class="form-control" :disabled="ev.locked"></textarea>
      </div>
      <template #footer>
        <template v-if="ev && !ev.locked && ev.rubrics.length">
          <button v-if="ev.status !== 'Submitted'" class="btn btn-outline-primary" @click="saveEval(false)">Save draft</button>
          <button class="btn btn-primary" @click="saveEval(true)">{{ ev.status === 'Submitted' ? 'Update' : 'Submit' }}</button>
        </template>
        <button class="btn btn-secondary" @click="ev = null">Cancel</button>
      </template>
    </modal-box>
  </div>`,
  data() {
    return { bookings: [], exams: [], examId: '', q: '', error: '', message: '', ev: null, evError: '' };
  },
  computed: {
    shown() { return this.limit ? this.bookings.slice(0, this.limit) : this.bookings; },
    total() { return this.ev ? this.ev.rubrics.reduce((sum, r) => sum + (Number(r.awarded) || 0), 0) : 0; },
  },
  async mounted() {
    if (!this.limit) { try { this.exams = await API.get('/examiner/exams'); } catch (e) { this.error = e.message; } }
    this.load();
  },
  methods: {
    evalBadge(s) { return 'badge bg-' + ({ Pending: 'warning', Draft: 'info', Submitted: 'success', Published: 'primary' }[s] || 'secondary'); },
    async load() {
      try { this.bookings = await API.get('/examiner/bookings?exam_id=' + this.examId + '&q=' + encodeURIComponent(this.q)); this.error = ''; }
      catch (e) { this.error = e.message; }
    },
    async openEval(b) {
      this.evError = '';
      try { this.ev = await API.get('/examiner/bookings/' + b.id + '/evaluation'); }
      catch (e) { this.error = e.message; }
    },
    async saveEval(submit) {
      const e = this.ev;
      const payload = { submit, remarks: e.remarks, scores: e.rubrics.map(r => ({ rubric_id: r.id, awarded_marks: r.awarded })) };
      try {
        await API.put('/examiner/bookings/' + e.booking.id + '/evaluation', payload);
        this.ev = null; this.error = '';
        this.message = submit ? 'Evaluation submitted' : 'Draft saved';
        await this.load(); this.$emit('changed');
      } catch (err) { this.evError = err.message; }
    },
  },
};
