const StudentExams = {
  components: { ExamDetail },
  template: `
  <div class="card shadow-sm">
    <div class="card-header fw-bold text-danger">Available Examinations</div>
    <div class="card-body border-bottom">
      <form class="row g-2" @submit.prevent="load">
        <div class="col-md-4"><input v-model.trim="q" class="form-control form-control-sm" placeholder="Search by exam or course"></div>
        <div class="col-md-3">
          <select v-model="examType" class="form-select form-select-sm">
            <option value="">All types</option>
            <option v-for="t in types" :key="t">{{ t }}</option>
          </select></div>
        <div class="col-md-3">
          <select v-model="courseId" class="form-select form-select-sm">
            <option value="">All courses</option>
            <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.code }} - {{ c.name }}</option>
          </select></div>
        <div class="col-md-2 d-flex gap-1">
          <button class="btn btn-sm btn-primary flex-fill">Search</button>
          <button type="button" class="btn btn-sm btn-outline-secondary" @click="reset">Reset</button>
        </div>
      </form>
    </div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Id</th><th>Course</th><th>Name</th><th>Type</th><th>Duration</th><th>Max marks</th><th>Open slots</th><th>Booking window</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="e in exams" :key="e.id">
            <td>{{ e.id }}</td><td>{{ e.course_code }}</td><td>{{ e.name }}</td><td>{{ e.exam_type }}</td>
            <td>{{ e.duration_minutes }} min</td><td>{{ e.max_marks }}</td><td>{{ e.open_slots }}</td>
            <td class="small">{{ $fmt(e.booking_start) }} to {{ $fmt(e.booking_end) }}</td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-outline-primary me-1" @click="viewId = e.id">View</button>
              <router-link v-if="e.bookable" class="btn btn-sm btn-success" :to="{ path: '/student/slots', query: { exam: e.id } }">Slots</router-link>
              <span v-else class="small" :class="e.booked ? 'text-success' : 'text-muted'">{{ e.booked ? 'Booked ' + e.my_slot : e.note }}</span>
            </td>
          </tr>
          <tr v-if="!exams.length"><td colspan="9" class="text-center text-muted">No examinations found</td></tr>
        </tbody>
      </table>
    </div>
    <exam-detail :exam-id="viewId" @close="viewId = null" />
  </div>`,
  data() {
    return { exams: [], courses: [], types: ['Viva', 'Practical', 'Project Demo', 'Assessment'],
             q: this.$route.query.q || '', examType: '', courseId: '', error: '', viewId: null };
  },
  watch: { '$route.query.q'(v) { this.q = v || ''; this.load(); } },   // navbar search
  async mounted() {
    try { this.courses = await API.get('/student/courses'); } catch (e) { this.error = e.message; }
    this.load();
  },
  methods: {
    async load() {
      const p = new URLSearchParams({ q: this.q, exam_type: this.examType, course_id: this.courseId });
      try { this.exams = await API.get('/student/exams?' + p.toString()); this.error = ''; }
      catch (e) { this.error = e.message; }
    },
    reset() { this.q = ''; this.examType = ''; this.courseId = ''; this.load(); },
  },
};
