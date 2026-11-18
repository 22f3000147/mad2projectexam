const AdminReports = {
  template: `
  <div class="row g-3">
    <div class="col-lg-7">
      <div class="card shadow-sm">
        <div class="card-header fw-bold text-danger">Monthly examination report</div>
        <div class="card-body">
          <p class="small text-muted">Celery Beat emails this to the admin on the 1st of every month. You can also generate any month now.</p>
          <div class="d-flex gap-2 mb-2">
            <input v-model="month" type="month" class="form-control form-control-sm w-auto">
            <button class="btn btn-sm btn-primary" :disabled="report.running" @click="runReport">
              {{ report.running ? 'Generating...' : 'Generate & email report' }}</button>
          </div>
          <div v-if="report.error" class="alert alert-danger py-2">{{ report.error }}</div>
          <div v-if="report.result">
            <div class="alert alert-success py-2">Report for {{ report.result.label }} is ready
              <span v-if="!report.result.emailed" class="text-muted">(mail server not configured, saved as a file)</span></div>
            <table class="table table-sm w-auto">
              <tbody>
                <tr><td>Examinations conducted</td><td><b>{{ report.result.stats.exams_conducted }}</b></td></tr>
                <tr><td>Participating students</td><td><b>{{ report.result.stats.participants }}</b></td></tr>
                <tr><td>Examiners involved</td><td><b>{{ report.result.stats.examiners_involved }}</b></td></tr>
                <tr><td>Students evaluated</td><td><b>{{ report.result.stats.students_evaluated }}</b></td></tr>
                <tr><td>Pending evaluations</td><td><b>{{ report.result.stats.pending_evaluations }}</b></td></tr>
              </tbody>
            </table>
            <button class="btn btn-sm btn-outline-primary" @click="openReport">Open full report</button>
          </div>
        </div>
      </div>
    </div>
    <div class="col-lg-5">
      <div class="card shadow-sm">
        <div class="card-header fw-bold text-danger">Daily exam reminders</div>
        <div class="card-body">
          <p class="small text-muted">Celery Beat sends reminders every morning to students whose exam is today or tomorrow (email, plus Google Chat if a webhook is set).</p>
          <button class="btn btn-sm btn-primary" :disabled="reminder.running" @click="runReminders">
            {{ reminder.running ? 'Sending...' : 'Run reminders now' }}</button>
          <div v-if="reminder.error" class="alert alert-danger py-2 mt-2">{{ reminder.error }}</div>
          <div v-if="reminder.result" class="alert alert-success py-2 mt-2">
            {{ reminder.result.reminders }} reminder(s) sent ({{ reminder.result.emailed }} by email, {{ reminder.result.webhooks }} on Google Chat).</div>
        </div>
      </div>
    </div>
  </div>`,
  data() {
    const d = new Date(); d.setDate(1); d.setMonth(d.getMonth() - 1);        // default = last month
    return { month: d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0'),
             report: { running: false, result: null, error: '' }, reminder: { running: false, result: null, error: '' } };
  },
  beforeUnmount() { this.gone = true; },
  methods: {
    async track(target, start) {
      target.running = true; target.result = null; target.error = '';
      try {
        const id = (await start()).task_id;
        for (let i = 0; i < 60 && !this.gone; i++) {
          await API.wait(1000);
          const s = await API.get('/admin/jobs/' + id);
          if (s.state === 'SUCCESS') { target.result = s.result; break; }
          if (s.state === 'FAILURE') throw new Error(s.error);
        }
        if (!target.result && !target.error && !this.gone) target.error = 'The job is taking long. Check the Celery worker.';
      } catch (e) { target.error = e.message; }
      finally { target.running = false; }
    },
    runReport() { return this.track(this.report, () => API.post('/admin/jobs/monthly-report', { month: this.month })); },
    runReminders() { return this.track(this.reminder, () => API.post('/admin/jobs/reminders')); },
    openReport() { API.openTab('/admin/reports/' + this.report.result.file).catch(e => { this.report.error = e.message; }); },
  },
};
