const StudentSlots = {
  props: { limit: Number },
  emits: ['changed'],
  template: `
  <div class="card shadow-sm mb-3">
    <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
      <span class="fw-bold text-danger">Available Slots</span>
      <router-link v-if="limit" to="/student/slots" class="btn btn-sm btn-link">View all</router-link>
      <select v-else v-model="examFilter" class="form-select form-select-sm w-auto" @change="load">
        <option value="">All exams</option>
        <option v-for="e in examOptions" :key="e.id" :value="e.id">{{ e.name }}</option>
      </select>
    </div>
    <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Id</th><th>Exam</th><th>Date</th><th>Time</th><th>Examiner</th><th>Max seats</th><th>Available</th><th>Status</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="s in shown" :key="s.id">
            <td>{{ s.id }}</td><td>{{ s.course_code }} - {{ s.exam_name }}</td><td>{{ s.date }}</td>
            <td>{{ s.start_time }} - {{ s.end_time }}</td><td>{{ s.examiner_name }}</td>
            <td>{{ s.max_capacity }}</td><td>{{ s.available_seats }}</td>
            <td><span :class="$badge(s.status)">{{ s.status }}</span></td>
            <td>
              <template v-if="s.my_booking_id">
                <button v-if="s.can_cancel" class="btn btn-sm btn-danger" @click="ask('cancel', s)">Cancel</button>
                <span v-else class="small text-success">Booked<span class="text-muted"> - {{ s.cancel_note }}</span></span>
              </template>
              <template v-else>
                <button v-if="s.can_book" class="btn btn-sm btn-success" @click="ask('book', s)">Book</button>
                <span v-else class="small text-muted">{{ s.note }}</span>
              </template>
            </td>
          </tr>
          <tr v-if="!shown.length"><td colspan="9" class="text-center text-muted">No slots open for booking right now</td></tr>
        </tbody>
      </table>
    </div>

    <modal-box :show="!!confirm" :title="confirm && confirm.type === 'book' ? 'Confirm booking' : 'Cancel booking'" @close="confirm = null">
      <div v-if="confirmError" class="alert alert-danger py-2">{{ confirmError }}</div>
      <p v-if="confirm" class="mb-0">
        {{ confirm.type === 'book' ? 'Do you want to book' : 'Do you want to cancel your booking for' }}
        <b>{{ confirm.slot.exam_name }}</b> on <b>{{ confirm.slot.date }}</b>,
        <b>{{ confirm.slot.start_time }} - {{ confirm.slot.end_time }}</b> with {{ confirm.slot.examiner_name }}?
      </p>
      <template #footer>
        <button class="btn" :class="confirm && confirm.type === 'book' ? 'btn-success' : 'btn-danger'" @click="run">Yes</button>
        <button class="btn btn-secondary" @click="confirm = null">No</button>
      </template>
    </modal-box>
  </div>`,
  data() {
    return { slots: [], examFilter: this.$route.query.exam ? Number(this.$route.query.exam) : '',
             error: '', message: '', confirm: null, confirmError: '' };
  },
  computed: {
    shown() {
      const rows = this.limit ? this.slots.filter(s => s.can_book || s.my_booking_id) : this.slots;
      return this.limit ? rows.slice(0, this.limit) : rows;
    },
    examOptions() {
      const seen = {};
      this.slots.forEach(s => { seen[s.examination_id] = { id: s.examination_id, name: s.exam_name }; });
      return Object.values(seen);
    },
  },
  mounted() { this.load(); },
  methods: {
    async load() {
      try { this.slots = await API.get('/student/slots' + (this.examFilter ? '?exam_id=' + this.examFilter : '')); }
      catch (e) { this.error = e.message; }
    },
    ask(type, slot) { this.confirmError = ''; this.confirm = { type, slot }; },
    async run() {
      const { type, slot } = this.confirm;
      try {
        if (type === 'book') await API.post('/student/bookings', { slot_id: slot.id });
        else await API.post('/student/bookings/' + slot.my_booking_id + '/cancel');
        this.confirm = null; this.error = '';
        this.message = type === 'book' ? 'Slot booked successfully' : 'Booking cancelled';
        await this.load(); this.$emit('changed');
      } catch (e) { this.confirmError = e.message; this.load(); }
    },
  },
};
