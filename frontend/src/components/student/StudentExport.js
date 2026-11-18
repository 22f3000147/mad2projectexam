const StudentExport = {
  template: `
  <div>
    <button class="btn btn-sm btn-outline-success" :disabled="busy" @click="start">
      {{ busy ? 'Preparing your export...' : 'Export history (CSV)' }}</button>
    <div v-if="error" class="alert alert-danger mt-2 py-2">{{ error }}</div>
    <div v-if="ready" class="alert alert-success mt-2 py-2 d-flex justify-content-between align-items-center">
      <span>Your export is ready ({{ rows }} rows).</span>
      <button class="btn btn-sm btn-success" @click="download">Download CSV</button>
    </div>
  </div>`,
  data() { return { busy: false, ready: false, taskId: null, rows: 0, error: '' }; },
  beforeUnmount() { this.gone = true; },
  methods: {
    async start() {
      this.error = ''; this.ready = false; this.busy = true;
      try {
        this.taskId = (await API.post('/student/export')).task_id;
        for (let i = 0; i < 60 && !this.gone; i++) {          // check every 1.5s, up to ~90s
          await API.wait(1500);
          const s = await API.get('/student/export/' + this.taskId);
          if (s.ready) { this.rows = s.rows; this.ready = true; break; }
          if (s.state === 'FAILURE') throw new Error('Export failed: ' + s.error);
        }
        if (!this.ready && !this.error && !this.gone) this.error = 'Export is taking long. Please try again.';
      } catch (e) { this.error = e.message; }
      finally { this.busy = false; }
    },
    download() {
      API.download('/student/export/' + this.taskId + '/download', 'exam_history.csv').catch(e => { this.error = e.message; });
    },
  },
};
