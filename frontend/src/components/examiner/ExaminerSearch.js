const ExaminerSearch = {
  template: `
  <div>
    <h5>Search results for "{{ $route.query.q }}"</h5>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="res">
      <div class="card mb-3" v-for="g in groups" :key="g.key">
        <div class="card-header py-1 fw-bold">{{ g.label }} ({{ res[g.key].length }})</div>
        <ul class="list-group list-group-flush">
          <li class="list-group-item py-1" v-for="r in res[g.key]" :key="r.id">{{ g.text(r) }}</li>
          <li class="list-group-item py-1 text-muted" v-if="!res[g.key].length">No match</li>
        </ul>
      </div>
    </div>
  </div>`,
  data() {
    return {
      res: null, error: '',
      groups: [
        { key: 'exams', label: 'My exams', text: r => '#' + r.id + ' ' + r.course_code + ' ' + r.name + ' - ' + r.status },
        { key: 'slots', label: 'My slots', text: r => '#' + r.id + ' ' + r.exam_name + ' ' + r.date + ' ' + r.start_time + '-' + r.end_time },
        { key: 'bookings', label: 'Booked students', text: r => 'Booking #' + r.id + ' ' + r.student_name + ' - ' + r.exam_name + ' (' + r.eval_status + ')' },
      ],
    };
  },
  watch: { '$route.query.q': { handler: 'load', immediate: true } },
  methods: {
    async load() {
      try { this.res = await API.get('/examiner/search?q=' + encodeURIComponent(this.$route.query.q || '')); this.error = ''; }
      catch (e) { this.res = null; this.error = e.message; }
    },
  },
};
