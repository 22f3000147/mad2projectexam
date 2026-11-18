const AdminBookings = {
  template: `
  <div class="card shadow-sm">
    <div class="card-header fw-bold text-danger">Registered Students</div>
    <div class="card-body border-bottom">
      <form class="row g-2" @submit.prevent="load">
        <div class="col-md-5"><label class="form-label mb-1">Select Exam Id</label>
          <select v-model="examId" class="form-select form-select-sm">
            <option value="">All exams</option>
            <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.id }} - {{ e.name }}</option>
          </select></div>
        <div class="col-md-5"><label class="form-label mb-1">Search by student Id / name</label>
          <input v-model.trim="q" class="form-control form-control-sm"></div>
        <div class="col-md-2 d-flex align-items-end"><button class="btn btn-sm btn-primary w-100">Search</button></div>
      </form>
    </div>
    <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Booking Id</th><th>Student</th><th>Course</th><th>Exam</th><th>Slot</th><th>Examiner</th><th>Status</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.id">
            <td>{{ b.id }}</td><td>{{ b.student_id }} - {{ b.student_name }}</td><td>{{ b.course_code }}</td>
            <td>{{ b.exam_name }}</td>
            <td>#{{ b.slot_id }} {{ b.slot_date }} {{ b.slot_start }}-{{ b.slot_end }}</td>
            <td>{{ b.examiner_name }}</td>
            <td><span :class="$badge(b.status)">{{ b.status }}</span></td>
            <td><button v-if="b.status === 'Booked' && !b.evaluated" class="btn btn-sm btn-outline-primary" @click="openReschedule(b)">Reschedule</button></td>
          </tr>
          <tr v-if="!bookings.length"><td colspan="8" class="text-center text-muted">No bookings found</td></tr>
        </tbody>
      </table>
    </div>

    <modal-box :show="!!target" :title="'Reschedule booking #' + (target ? target.id : '')" @close="target = null">
      <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
      <div v-if="target">
        <p class="mb-2">{{ target.student_name }} - {{ target.exam_name }}</p>
        <label class="form-label mb-1">Move to slot</label>
        <select v-model="newSlot" class="form-select">
          <option value="" disabled>Select a slot</option>
          <option v-for="s in openSlots" :key="s.id" :value="s.id">
            #{{ s.id }} {{ s.date }} {{ s.start_time }}-{{ s.end_time }} ({{ s.examiner_name }}, {{ s.available_seats }} seats left)
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
    return { bookings: [], exams: [], examId: '', q: '', error: '', message: '',
             target: null, openSlots: [], newSlot: '', formError: '' };
  },
  async mounted() {
    try { this.exams = await API.get('/admin/exams'); } catch (e) { this.error = e.message; }
    this.load();
  },
  methods: {
    async load() {
      try {
        this.bookings = await API.get('/admin/bookings?exam_id=' + this.examId + '&q=' + encodeURIComponent(this.q));
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
