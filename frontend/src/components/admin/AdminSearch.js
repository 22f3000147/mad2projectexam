const AdminSearch = {
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
        { key: 'students', label: 'Students', text: r => '#' + r.id + ' ' + r.name + ' (' + r.email + ')' },
        { key: 'examiners', label: 'Examiners', text: r => '#' + r.id + ' ' + r.name + ' (' + r.email + ') - ' + r.status },
        { key: 'exams', label: 'Examinations', text: r => '#' + r.id + ' ' + r.course_code + ' ' + r.name + ' - ' + r.status },
        { key: 'bookings', label: 'Bookings', text: r => '#' + r.id + ' ' + r.student_name + ' - ' + r.exam_name + ' - ' + r.status },
      ],
    };
  },
  watch: { '$route.query.q': { handler: 'load', immediate: true } },
  methods: {
    async load() {
      try { this.res = await API.get('/admin/search?q=' + encodeURIComponent(this.$route.query.q || '')); this.error = ''; }
      catch (e) { this.res = null; this.error = e.message; }
    },
  },
};
