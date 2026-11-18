const ExaminerDashboard = {
  template: `
  <div>
    <nav class="navbar navbar-expand bg-info-subtle border-bottom px-3 flex-wrap">
      <ul class="navbar-nav me-auto flex-wrap">
        <li class="nav-item" v-for="l in links" :key="l.to">
          <router-link class="nav-link" :to="l.to" exact-active-class="active fw-bold">{{ l.label }}</router-link>
        </li>
      </ul>
      <form class="d-flex my-1" @submit.prevent="search">
        <input v-model.trim="q" class="form-control form-control-sm" placeholder="Search anything here...">
        <button class="btn btn-sm btn-primary ms-2">Search</button>
      </form>
    </nav>
    <div class="container-fluid py-3"><router-view /></div>
  </div>`,
  data() {
    return {
      q: '',
      links: [
        { to: '/examiner', label: 'Home' },
        { to: '/examiner/exams', label: 'Exams' },
        { to: '/examiner/slots', label: 'Slots' },
        { to: '/examiner/bookings', label: 'Booked Students' },
      ],
    };
  },
  methods: {
    search() { if (this.q) this.$router.push({ path: '/examiner/search', query: { q: this.q } }); },
  },
};
