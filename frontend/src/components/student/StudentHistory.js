const StudentHistory = {
  components: { ExamDetail, StudentExport },
  template: `
  <div class="card shadow-sm">
    <div class="card-header d-flex justify-content-between align-items-start">
      <span class="fw-bold text-danger">History and Scores</span>
      <student-export />
    </div>
    <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
    <div class="table-responsive">
      <table class="table table-sm table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>Booking Id</th><th>Course</th><th>Exam</th><th>Date</th><th>Examiner</th><th>Booking status</th><th>Result</th><th>Action</th>
        </tr></thead>
        <tbody>
          <tr v-for="b in rows" :key="b.id">
            <td>{{ b.id }}</td><td>{{ b.course_code }}</td><td>{{ b.exam_name }}</td>
            <td>{{ b.slot_date }} {{ b.slot_start }}</td><td>{{ b.examiner_name }}</td>
            <td><span :class="$badge(b.status)">{{ b.status }}</span></td>
            <td>
              <b v-if="b.result">{{ b.result.total }} / {{ b.result.max }}</b>
              <span v-else-if="b.status !== 'Cancelled'" class="small text-muted">{{ b.result_status }}</span>
            </td>
            <td class="text-nowrap">
              <button v-if="b.result" class="btn btn-sm btn-outline-success me-1" @click="shown = b">Feedback</button>
              <button class="btn btn-sm btn-outline-primary" @click="viewId = b.exam_id">Exam</button>
            </td>
          </tr>
          <tr v-if="!rows.length"><td colspan="8" class="text-center text-muted">No exam history yet</td></tr>
        </tbody>
      </table>
    </div>

    <modal-box :show="!!shown" title="Result and feedback" @close="shown = null">
      <div v-if="shown && shown.result">
        <p class="mb-2"><b>{{ shown.exam_name }}</b> ({{ shown.course_code }}) - examiner {{ shown.result.examiner }}<br><span class="small text-muted">Evaluated on {{ $fmt(shown.result.date) }}</span></p>
        <table class="table table-sm">
          <thead><tr><th>Criteria</th><th>Awarded</th><th>Max</th></tr></thead>
          <tbody><tr v-for="s in shown.result.scores" :key="s.criterion">
            <td>{{ s.criterion }}</td><td>{{ s.awarded }}</td><td>{{ s.max }}</td></tr></tbody>
        </table>
        <div class="fw-bold mb-2">Total: {{ shown.result.total }} / {{ shown.result.max }}</div>
        <div><b>Examiner remarks</b></div>
        <div class="border rounded p-2 bg-light">{{ shown.result.remarks }}</div>
      </div>
      <template #footer><button class="btn btn-secondary" @click="shown = null">Close</button></template>
    </modal-box>
    <exam-detail :exam-id="viewId" @close="viewId = null" />
  </div>`,
  data() { return { rows: [], error: '', shown: null, viewId: null }; },
  async mounted() {
    try { this.rows = await API.get('/student/bookings?history=1'); }
    catch (e) { this.error = e.message; }
  },
};
