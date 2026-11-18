const ExaminerHome = {
  components: { ExaminerExams, ExaminerBookings },
  template: `
  <div>
    <div class="row g-2 mb-3">
      <div class="col-6 col-md-3" v-for="c in cards" :key="c.key">
        <div class="card text-center shadow-sm"><div class="card-body py-2">
          <div class="fs-3 fw-bold">{{ stats[c.key] === undefined ? '-' : stats[c.key] }}</div>
          <div class="small text-muted">{{ c.label }}</div>
        </div></div>
      </div>
    </div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <examiner-exams :limit="5" @changed="loadStats" />
    <examiner-bookings :limit="5" @changed="loadStats" />
  </div>`,
  data() {
    return {
      stats: {}, error: '',
      cards: [
        { key: 'assigned_exams', label: 'Assigned exams' }, { key: 'slots', label: 'Slots created' },
        { key: 'students_booked', label: 'Students booked' }, { key: 'pending_evaluations', label: 'Pending evaluations' },
      ],
    };
  },
  mounted() { this.loadStats(); },
  methods: {
    async loadStats() {
      try { this.stats = await API.get('/examiner/dashboard'); }
      catch (e) { this.error = e.message; }
    },
  },
};
