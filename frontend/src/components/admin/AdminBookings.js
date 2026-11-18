const AdminBookings = {
  template: `
  <div class="card shadow-sm">
    <div class="card-header fw-bold text-danger">Registered Students</div>
    <div class="card-body border-bottom">
      <form class="row g-2" @submit.prevent="load">
        <div class="col-md-4"><label class="form-label mb-1">Select Exam Id</label>
          <select v-model="examId" class="form-select form-select-sm">
            <option value="">All exams</option>
            <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.id }} - {{ e.name }}</option>
          </select></div>
        <div class="col-md-3"><label class="form-label mb-1">Search by student Id / name</label>
          <input v-model.trim="q" class="form-control form-control-sm"></div>
        <div class="col-md-3"><label class="form-label mb-1">Booking status</label>
          <select v-model="statusFilter" class="form-select form-select-sm">
            <option value="">All (full history)</option>
            <option>Booked</option><option>Completed</option><option>Cancelled</option>
          </select></div>
        <div class="col-md-2 d-flex align-items-end"><button class="btn btn-sm btn-primary w-100">Search</button></div>
      </form>
    </div>
    <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Booking Id</th><th>Student</th><th>Course</th><th>Exam</th><th>Slot</th><th>Examiner</th><th>Status</th><th>Evaluation</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.id">
            <td>{{ b.id }}</td><td>{{ b.student_id }} - {{ b.student_name }}</td><td>{{ b.course_code }}</td>
            <td>{{ b.exam_name }}</td>
            <td>#{{ b.slot_id }} {{ b.slot_date }} {{ b.slot_start }}-{{ b.slot_end }}</td>
            <td>{{ b.examiner_name }}</td>
            <td><span :class="$badge(b.status)">{{ b.status }}</span></td>
            <td><span :class="evalBadge(b.eval_status)">{{ b.eval_status }}</span>
              <span v-if="b.marks !== null" class="ms-1">{{ b.marks }} / {{ b.max_marks }}</span></td>
            <td class="text-nowrap">
              <button v-if="b.eval_status !== 'Pending'" class="btn btn-sm btn-outline-success me-1" @click="openEval(b)">View</button>
              <button v-if="b.status === 'Booked' && !b.evaluated" class="btn btn-sm btn-outline-primary" @click="openReschedule(b)">Reschedule</button>
            </td>
          </tr>
          <tr v-if="!bookings.length"><td colspan="9" class="text-center text-muted">No bookings found</td></tr>
        </tbody>
      </table>
    </div>

    <modal-box :show="!!evalView" title="Evaluation" @close="evalView = null">
      <div v-if="evalView">
        <p class="mb-1"><b>{{ evalView.booking.student_name }}</b> - {{ evalView.booking.exam_name }}
          <span :class="evalBadge(evalView.status)">{{ evalView.status }}</span></p>
        <p class="small text-muted">Examiner {{ evalView.examiner }} - {{ $fmt(evalView.date) }}</p>
        <table class="table table-sm">
          <thead><tr><th>Criteria</th><th>Awarded</th><th>Max</th></tr></thead>
          <tbody><tr v-for="s in evalView.scores" :key="s.criterion"><td>{{ s.criterion }}</td><td>{{ s.awarded }}</td><td>{{ s.max }}</td></tr></tbody>
        </table>
        <div class="fw-bold mb-2">Total: {{ evalView.total }} / {{ evalView.booking.max_marks }}</div>
        <div><b>Remarks</b></div><div class="border rounded p-2 bg-light">{{ evalView.remarks || '-' }}</div>
      </div>
      <template #footer><button class="btn btn-secondary" @click="evalView = null">Close</button></template>
    </modal-box>

    <modal-box :show="!!target" :title="'Reschedule booking #' + (target ? target.id : '')" @close="target = null">
      <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
      <div v-if="target">
        <p class="mb-2">{{ target.student_name }} - {{ target.exam_name }}</p>
        <label class="form-label mb-1">Move to slot</label>
        <select v-model="newSlot" class="form-select">
          <option value="" disabled>Select a slot</option>
          <option v-for="s in openSlots" :key="s.id" :value="s.id">
          </option>
        </select>
        <div v-if="!openSlots.length" class="form-text text-danger">No other open slots for this exam.</div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="reschedule">Update</button>
        <button class="btn btn-secondary" @click="target = null">Cancel</button>
      </template>
    </modal-box>
  </div>`,
  data() {
    return { bookings: [], exams: [], examId: '', q: '', statusFilter: '', evalView: null, error: '', message: '',
             target: null, openSlots: [], newSlot: '', formError: '' };
  },
  async mounted() {
    try { this.exams = await API.get('/admin/exams'); } catch (e) { this.error = e.message; }
    this.load();
  },
  methods: {
    evalBadge(s) { return 'badge bg-' + ({ Pending: 'warning', Draft: 'info', Submitted: 'success', Published: 'primary' }[s] || 'secondary'); },
    async openEval(b) {
      try { this.evalView = await API.get('/admin/bookings/' + b.id + '/evaluation'); }
      catch (e) { this.error = e.message; }
    },
    async load() {
      try {
        this.bookings = await API.get('/admin/bookings?exam_id=' + this.examId + '&status=' + this.statusFilter + '&q=' + encodeURIComponent(this.q));
        this.error = '';
      } catch (e) { this.error = e.message; }
    },
    async openReschedule(b) {
      this.formError = ''; this.newSlot = ''; this.target = b;
      const slots = await API.get('/admin/slots?open=1&exam_id=' + b.examination_id);
      this.openSlots = slots.filter(s => s.id !== b.slot_id);
    },
    async reschedule() {
      try {
        await API.put('/admin/bookings/' + this.target.id + '/reschedule', { slot_id: this.newSlot });
        this.target = null; this.message = 'Booking rescheduled';
        await this.load();
      } catch (e) { this.formError = e.message; }
    },
  },
};
