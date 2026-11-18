const AdminExams = {
  props: { limit: Number },
  emits: ['changed'],
  template: `
  <div>
    <div class="card shadow-sm mb-3">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span class="fw-bold text-danger">Examinations</span>
        <div>
          <router-link v-if="limit" to="/admin/exams" class="btn btn-sm btn-link">View all</router-link>
          <button class="btn btn-sm btn-success" @click="openNew">+ New Exam</button>
        </div>
      </div>
      <div v-if="message" class="alert alert-success m-2 py-2">{{ message }}</div>
      <div v-if="error" class="alert alert-danger m-2 py-2">{{ error }}</div>
      <div class="table-responsive">
        <table class="table table-sm table-hover mb-0 align-middle">
          <thead class="table-light"><tr>
            <th>Id</th><th>Course</th><th>Name</th><th>Type</th><th>Duration</th><th>Max marks</th>
            <th>Status</th><th>Action</th>
          </tr></thead>
          <tbody>
            <tr v-for="e in shown" :key="e.id">
              <td>{{ e.id }}</td><td>{{ e.course_code }}</td><td>{{ e.name }}</td><td>{{ e.exam_type }}</td>
              <td>{{ e.duration_minutes }} min</td><td>{{ e.max_marks }}</td>
              <td>
                <span :class="$badge(e.status)">{{ e.status }}</span>
                <div class="mt-1">
                  <button v-for="n in e.next" :key="n.to" class="btn btn-sm btn-outline-dark py-0 me-1 mb-1"
                          @click="changeStatus(e, n.to)">{{ n.label }}</button>
                </div>
                <div v-if="e.evaluated_count" class="small text-muted">Evaluated: {{ e.evaluated_count }}
                  <span v-if="e.results_published && !e.unpublished_count" class="badge bg-primary">Results published</span></div>
                <button v-if="e.status === 'Completed' && e.unpublished_count" class="btn btn-sm btn-primary py-0 mt-1"
                        @click="publish(e)">Publish results ({{ e.unpublished_count }})</button>
              </td>
              <td>
                <div class="d-flex flex-wrap gap-1">
                  <button class="btn btn-sm btn-outline-primary" @click="openEdit(e)">Edit</button>
                  <button class="btn btn-sm btn-outline-info" @click="openRubrics(e)">Rubrics ({{ e.rubric_count }})</button>
                  <button class="btn btn-sm btn-outline-secondary" @click="openAssign(e)">Examiners ({{ e.examiners.length }})</button>
                  <router-link class="btn btn-sm btn-outline-success" :to="{ path: '/admin/slots', query: { exam: e.id } }">Slots ({{ e.slot_count }})</router-link>
                  <button class="btn btn-sm btn-outline-danger" @click="remove(e)">Delete</button>
                </div>
              </td>
            </tr>
            <tr v-if="!shown.length"><td colspan="8" class="text-center text-muted">No examinations yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <modal-box :show="!!form" :title="form && form.id ? 'Edit Examination' : 'New Examination'" size="modal-lg" @close="form = null">
      <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
      <div v-if="form" class="row g-2">
        <div class="col-md-6"><label class="form-label mb-1">Course code</label>
          <select v-model="form.course_id" class="form-select">
            <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.code }} - {{ c.name }}</option>
          </select></div>
        <div class="col-md-6"><label class="form-label mb-1">Name</label>
          <input v-model.trim="form.name" class="form-control"></div>
        <div class="col-md-4"><label class="form-label mb-1">Type</label>
          <select v-model="form.exam_type" class="form-select">
            <option v-for="t in types" :key="t">{{ t }}</option>
          </select></div>
        <div class="col-md-4"><label class="form-label mb-1">Duration (min)</label>
          <input v-model.number="form.duration_minutes" type="number" min="1" class="form-control"></div>
        <div class="col-md-4"><label class="form-label mb-1">Max marks</label>
          <input v-model.number="form.max_marks" type="number" min="1" class="form-control"></div>
        <div class="col-12"><label class="form-label mb-1">Instructions</label>
          <textarea v-model="form.instructions" rows="2" class="form-control"></textarea></div>
        <div class="col-12 fw-bold mt-2">Timelines</div>
        <div class="col-md-6"><label class="form-label mb-1">Slot creation start</label>
          <input v-model="form.slot_creation_start" type="datetime-local" class="form-control"></div>
        <div class="col-md-6"><label class="form-label mb-1">Slot creation end</label>
          <input v-model="form.slot_creation_end" type="datetime-local" class="form-control"></div>
        <div class="col-md-6"><label class="form-label mb-1">Booking start</label>
          <input v-model="form.booking_start" type="datetime-local" class="form-control"></div>
        <div class="col-md-6"><label class="form-label mb-1">Booking end</label>
          <input v-model="form.booking_end" type="datetime-local" class="form-control"></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="save">Update</button>
        <button class="btn btn-secondary" @click="form = null">Cancel</button>
      </template>
    </modal-box>

    <modal-box :show="!!rubricExam" :title="'Rubrics - ' + (rubricExam ? rubricExam.name : '')" size="modal-lg" @close="rubricExam = null">
      <div v-if="rubricError" class="alert alert-danger py-2">{{ rubricError }}</div>
      <table class="table table-sm align-middle">
        <thead><tr><th>Criteria</th><th>Max marks</th><th>Weightage</th><th>Description</th><th></th></tr></thead>
        <tbody>
          <tr v-for="r in rubrics" :key="r.id">
            <td>{{ r.criterion_name }}</td><td>{{ r.max_marks }}</td><td>{{ r.weightage }}</td><td>{{ r.description }}</td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-outline-primary me-1" @click="rubricForm = { ...r }">Edit</button>
              <button class="btn btn-sm btn-outline-danger" @click="removeRubric(r)">Delete</button>
            </td>
          </tr>
          <tr v-if="!rubrics.length"><td colspan="5" class="text-muted text-center">No rubric criteria yet</td></tr>
        </tbody>
      </table>
      <div class="small mb-2">Total {{ rubricTotal }} / {{ rubricExam ? rubricExam.max_marks : 0 }} marks used</div>
      <div class="border rounded p-2 bg-light">
        <div class="fw-bold mb-1">{{ rubricForm.id ? 'Edit criteria' : 'Add criteria' }}</div>
        <div class="row g-2">
          <div class="col-md-6"><input v-model.trim="rubricForm.criterion_name" class="form-control" placeholder="Criteria name"></div>
          <div class="col-md-3"><input v-model.number="rubricForm.max_marks" type="number" min="1" class="form-control" placeholder="Max marks"></div>
          <div class="col-md-3"><input v-model.number="rubricForm.weightage" type="number" step="0.1" min="0.1" class="form-control" placeholder="Weightage"></div>
          <div class="col-12"><input v-model.trim="rubricForm.description" class="form-control" placeholder="Description"></div>
        </div>
        <button class="btn btn-sm btn-primary mt-2 me-1" @click="saveRubric">{{ rubricForm.id ? 'Update' : 'Add' }}</button>
        <button v-if="rubricForm.id" class="btn btn-sm btn-secondary mt-2" @click="rubricForm = blankRubric()">Cancel</button>
      </div>
      <template #footer><button class="btn btn-secondary" @click="rubricExam = null">Close</button></template>
    </modal-box>

    <modal-box :show="!!assignExam" :title="'Examiners - ' + (assignExam ? assignExam.name : '')" @close="assignExam = null">
      <div v-if="assignError" class="alert alert-danger py-2">{{ assignError }}</div>
      <div v-if="!approved.length" class="text-muted">No approved examiners yet. Add one in the Examiners table.</div>
      <div class="form-check" v-for="x in approved" :key="x.id">
        <input class="form-check-input" type="checkbox" :id="'ax' + x.id" :value="x.id" v-model="assignIds">
        <label class="form-check-label" :for="'ax' + x.id">{{ x.name }} <span class="text-muted small">({{ x.department || 'no dept' }})</span></label>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="saveAssign">Update</button>
        <button class="btn btn-secondary" @click="assignExam = null">Cancel</button>
      </template>
    </modal-box>
  </div>`,
  data() {
    return {
      exams: [], courses: [], examiners: [],
      types: ['Viva', 'Practical', 'Project Demo', 'Assessment'],
      form: null, formError: '', error: '', message: '',
      rubricExam: null, rubrics: [], rubricTotal: 0, rubricForm: this.blankRubric(), rubricError: '',
      assignExam: null, assignIds: [], assignError: '',
    };
  },
  computed: {
    shown() { return this.limit ? this.exams.slice(0, this.limit) : this.exams; },
    approved() { return this.examiners.filter(x => x.status === 'Approved'); },
  },
  mounted() { this.load(); },
  methods: {
    blankRubric() { return { id: null, criterion_name: '', max_marks: '', weightage: 1, description: '' }; },
    async load() {
      try {
        [this.exams, this.courses, this.examiners] = await Promise.all([
          API.get('/admin/exams'), API.get('/admin/courses'), API.get('/admin/examiners')]);
      } catch (e) { this.error = e.message; }
    },
    done(msg) { this.error = ''; this.message = msg; this.$emit('changed'); return this.load(); },
    fail(e) { this.message = ''; this.error = e.message; },

    openNew() {
      this.formError = '';
      this.form = { id: null, course_id: this.courses.length ? this.courses[0].id : '', name: '', exam_type: 'Viva',
        duration_minutes: 30, max_marks: 100, instructions: '',
        slot_creation_start: '', slot_creation_end: '', booking_start: '', booking_end: '' };
    },
    openEdit(e) { this.formError = ''; this.form = { ...e }; },
    async save() {
      const f = this.form;
      try {
        if (f.id) await API.put('/admin/exams/' + f.id, f);
        else await API.post('/admin/exams', f);
        this.form = null;
        await this.done('Examination saved');
      } catch (e) { this.formError = e.message; }
    },
    async remove(e) {
      if (!confirm('Delete exam ' + e.name + '?')) return;
      try { await API.del('/admin/exams/' + e.id); await this.done('Examination deleted'); }
      catch (err) { this.fail(err); }
    },
    async changeStatus(e, to) {
      try { await API.post('/admin/exams/' + e.id + '/status', { status: to }); await this.done(e.name + ' is now ' + to); }
      catch (err) { this.fail(err); }
    },

    async publish(e) {
      if (!confirm('Publish results of ' + e.name + '? Students will see their marks and remarks.')) return;
      try {
        const res = await API.post('/admin/exams/' + e.id + '/publish');
        await this.done('Results published for ' + res.published + ' student(s)');
      } catch (err) { this.fail(err); }
    },

    async openRubrics(e) { this.rubricExam = e; this.rubricForm = this.blankRubric(); this.rubricError = ''; await this.loadRubrics(); },
    async loadRubrics() {
      const res = await API.get('/admin/exams/' + this.rubricExam.id + '/rubrics');
      this.rubrics = res.rubrics; this.rubricTotal = res.total;
    },
    async saveRubric() {
      const f = this.rubricForm;
      try {
        if (f.id) await API.put('/admin/rubrics/' + f.id, f);
        else await API.post('/admin/exams/' + this.rubricExam.id + '/rubrics', f);
        this.rubricForm = this.blankRubric(); this.rubricError = '';
        await this.loadRubrics(); await this.load();
      } catch (e) { this.rubricError = e.message; }
    },
    async removeRubric(r) {
      if (!confirm('Delete this criteria?')) return;
      try { await API.del('/admin/rubrics/' + r.id); await this.loadRubrics(); await this.load(); }
      catch (e) { this.rubricError = e.message; }
    },

    openAssign(e) { this.assignError = ''; this.assignExam = e; this.assignIds = e.examiners.map(x => x.id); },
    async saveAssign() {
      try {
        await API.put('/admin/exams/' + this.assignExam.id + '/examiners', { examiner_ids: this.assignIds });
        this.assignExam = null;
        await this.done('Examiners updated');
      } catch (e) { this.assignError = e.message; }
    },
  },
};
