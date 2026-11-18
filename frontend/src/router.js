const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginView, meta: { guest: true } },
  { path: '/register', component: RegisterView, meta: { guest: true } },
  {
    path: '/admin', component: AdminDashboard, meta: { role: 'admin' },
    children: [
      { path: '', component: AdminHome },
      { path: 'courses', component: AdminCourses },
      { path: 'exams', component: AdminExams },
      { path: 'examiners', component: AdminExaminers },
      { path: 'students', component: AdminStudents },
      { path: 'slots', component: AdminSlots },
      { path: 'bookings', component: AdminBookings },
      { path: 'search', component: AdminSearch },
    ],
  },
  {
    path: '/examiner', component: ExaminerDashboard, meta: { role: 'examiner' },
    children: [
      { path: '', component: ExaminerHome },
      { path: 'exams', component: ExaminerExams },
      { path: 'slots', component: ExaminerSlots },
      { path: 'bookings', component: ExaminerBookings },
      { path: 'search', component: ExaminerSearch },
    ],
  },
  {
    path: '/student', component: StudentDashboard, meta: { role: 'student' },
    children: [
      { path: '', component: StudentHome },
      { path: 'exams', component: StudentExams },
      { path: 'slots', component: StudentSlots },
      { path: 'history', component: StudentHistory },
      { path: 'profile', component: StudentProfile },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
];

const router = VueRouter.createRouter({
  history: VueRouter.createWebHashHistory(),
  routes,
});

const HOME = { admin: '/admin', examiner: '/examiner', student: '/student' };

router.beforeEach((to) => {
  if (to.meta.guest) return authStore.isLoggedIn ? HOME[authStore.role] : true;
  if (to.meta.role) {
    if (!authStore.isLoggedIn) return '/login';
    if (authStore.role !== to.meta.role) return HOME[authStore.role];
  }
  return true;
});
