
const AdminHome = {
  components: { AdminCourses, AdminExams, AdminExaminers },
  template: `
  <div>
    <div class="row g-2 mb-3">
      <div class="col-6 col-md-2" v-for="c in cards" :key="c.key">
        <div class="card text-center shadow-sm"><div class="card-body py-2">
          <div class="fs-3 fw-bold">{{ stats[c.key] === undefined ? '-' : stats[c.key] }}</div>
          <div class="small text-muted">{{ c.label }}</div>
        </div></div>
      </div>
    </div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <admin-courses :limit="5" @changed="loadStats" />
    <admin-exams :limit="5" @changed="loadStats" />
    <admin-examiners :limit="5" @changed="loadStats" />
  </div>`,
  data() {
    return {
      stats: {}, error: '',
      cards: [
        { key: 'courses', label: 'Courses' }, { key: 'examinations', label: 'Examinations' },
        { key: 'examiners', label: 'Examiners' }, { key: 'students', label: 'Students' },
        { key: 'slots', label: 'Exam slots' }, { key: 'bookings', label: 'Bookings' },
      ],
    };
  },
  mounted() { this.loadStats(); },
  methods: {
    async loadStats() {
      try { this.stats = await API.get('/admin/dashboard'); }
      catch (e) { this.error = e.message; }
    },
  },
};
