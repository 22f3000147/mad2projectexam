const StudentUpcoming = {
  props: { limit: Number },
  template: `
  <div class="card shadow-sm mb-3">
    <div class="card-header fw-bold text-danger">Upcoming Exams</div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Booking Id</th><th>Course</th><th>Exam</th><th>Date</th><th>Time</th><th>Examiner</th><th>Type</th><th>Duration</th><th>Max marks</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="b in shown" :key="b.id">
            <td>{{ b.id }}</td><td>{{ b.course_code }}</td><td>{{ b.exam_name }}</td><td>{{ b.slot_date }}</td>
            <td>{{ b.slot_start }} - {{ b.slot_end }}</td><td>{{ b.examiner_name }}</td><td>{{ b.exam_type }}</td>
            <td>{{ b.duration_minutes }} min</td><td>{{ b.max_marks }}</td>
            <td><button class="btn btn-sm btn-outline-primary" @click="viewId = b.exam_id">View</button></td>
          </tr>
          <tr v-if="!shown.length"><td colspan="10" class="text-center text-muted">No upcoming exams. Book a slot to see it here.</td></tr>
        </tbody>
      </table>
    </div>
    <exam-detail :exam-id="viewId" @close="viewId = null" />
  </div>`,
  components: { ExamDetail },
  data() { return { rows: [], error: '', viewId: null }; },
  computed: { shown() { return this.limit ? this.rows.slice(0, this.limit) : this.rows; } },
  async mounted() {
    try { this.rows = await API.get('/student/bookings?upcoming=1'); }
    catch (e) { this.error = e.message; }
  },
};
