const StudentHome = {
  components: { StudentSlots, StudentUpcoming, StudentExport },
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
    <div class="mb-3"><student-export /></div>
    <student-slots :limit="5" @changed="refresh" />
    <student-upcoming :limit="5" :key="upcomingKey" />
  </div>`,
  data() {
    return {
      stats: {}, error: '', upcomingKey: 0,
      cards: [
        { key: 'available_exams', label: 'Available exams' }, { key: 'available_slots', label: 'Available slots' },
        { key: 'upcoming', label: 'Upcoming exams' }, { key: 'results', label: 'Published results' },
      ],
    };
  },
  mounted() { this.loadStats(); },
  methods: {
    async loadStats() {
      try { this.stats = await API.get('/student/dashboard'); }
      catch (e) { this.error = e.message; }
    },
    refresh() { this.loadStats(); this.upcomingKey++; },     // re-mount Upcoming so it reloads
  },
};
