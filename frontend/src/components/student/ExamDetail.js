const ExamDetail = {
  props: { examId: Number },
  emits: ['close'],
  template: `
  <modal-box :show="!!examId" title="Examination details" size="modal-lg" @close="$emit('close')">
    <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
    <div v-if="exam">
      <h5 class="mb-1">{{ exam.name }} <span class="badge bg-secondary">{{ exam.exam_type }}</span></h5>
      <div class="text-muted mb-2">{{ exam.course_code }} - {{ exam.course_name }}</div>
      <div class="row small mb-2">
        <div class="col-md-4"><b>Duration:</b> {{ exam.duration_minutes }} min</div>
        <div class="col-md-4"><b>Max marks:</b> {{ exam.max_marks }}</div>
        <div class="col-md-4"><b>Status:</b> <span :class="$badge(exam.status)">{{ exam.status }}</span></div>
        <div class="col-md-12 mt-1"><b>Booking window:</b> {{ $fmt(exam.booking_start) }} to {{ $fmt(exam.booking_end) }}</div>
      </div>
      <div v-if="exam.instructions" class="mb-2"><b>Instructions</b><div class="border rounded p-2 bg-light small">{{ exam.instructions }}</div></div>
      <div v-if="exam.rubrics.length">
        <b>Evaluation criteria</b>
        <table class="table table-sm mt-1">
          <thead><tr><th>Criteria</th><th>Max marks</th><th>Description</th></tr></thead>
          <tbody><tr v-for="r in exam.rubrics" :key="r.criterion_name">
            <td>{{ r.criterion_name }}</td><td>{{ r.max_marks }}</td><td>{{ r.description }}</td></tr></tbody>
        </table>
      </div>
    </div>
    <template #footer>
      <router-link v-if="exam && exam.bookable" class="btn btn-success" :to="{ path: '/student/slots', query: { exam: exam.id } }" @click="$emit('close')">View slots</router-link>
      <button class="btn btn-secondary" @click="$emit('close')">Close</button>
    </template>
  </modal-box>`,
  data() { return { exam: null, error: '' }; },
  watch: { examId: { handler: 'load', immediate: true } },
  methods: {
    async load() {
      this.exam = null; this.error = '';
      if (!this.examId) return;
      try { this.exam = await API.get('/student/exams/' + this.examId); }
      catch (e) { this.error = e.message; }
    },
  },
};
