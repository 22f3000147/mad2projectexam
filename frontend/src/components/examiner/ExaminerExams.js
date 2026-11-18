const ExaminerExams = {
  props: { limit: Number },
  emits: ['changed'],
  template: `
  <div class="card shadow-sm mb-3">
    <div class="card-header d-flex justify-content-between align-items-center">
      <span class="fw-bold text-danger">Assigned Exams</span>
      <router-link v-if="limit" to="/examiner/exams" class="btn btn-sm btn-link">View all</router-link>
    </div>
    <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Id</th><th>Course</th><th>Name</th><th>Type</th><th>Duration</th><th>Max marks</th>
          <th>Status</th><th>My slots</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="e in shown" :key="e.id">
            <td>{{ e.id }}</td><td>{{ e.course_code }}</td>
            <td>{{ e.name }}
              <div class="small text-muted">Slot creation: {{ $fmt(e.slot_creation_start) }} to {{ $fmt(e.slot_creation_end) }}</div>
            </td>
            <td>{{ e.exam_type }}</td><td>{{ e.duration_minutes }} min</td><td>{{ e.max_marks }}</td>
            <td><span :class="$badge(e.status)">{{ e.status }}</span></td>
            <td>{{ e.my_slots }} ({{ e.my_students }} students)</td>
            <td>
              <router-link v-if="e.can_create_slots" class="btn btn-sm btn-success"
                           :to="{ path: '/examiner/slots', query: { exam: e.id, new: 1 } }">+ Fill availability</router-link>
              <span v-else class="small text-muted">{{ e.slot_note }}</span>
              <button v-if="e.status === 'Closed'" class="btn btn-sm btn-outline-dark ms-1" @click="complete(e)">Mark completed</button>
            </td>
          </tr>
          <tr v-if="!shown.length"><td colspan="9" class="text-center text-muted">No exams assigned to you yet</td></tr>
        </tbody>
      </table>
    </div>
  </div>`,
  data() { return { exams: [], error: '', message: '' }; },
  computed: { shown() { return this.limit ? this.exams.slice(0, this.limit) : this.exams; } },
  mounted() { this.load(); },
  methods: {
    async load() {
      try { this.exams = await API.get('/examiner/exams'); }
      catch (e) { this.error = e.message; }
    },
    async complete(e) {
      if (!confirm('Mark ' + e.name + ' as completed? Slots will be locked.')) return;
      try {
        await API.post('/examiner/exams/' + e.id + '/complete');
        this.error = ''; this.message = e.name + ' marked as completed';
        await this.load(); this.$emit('changed');
      } catch (err) { this.message = ''; this.error = err.message; }
    },
  },
};
