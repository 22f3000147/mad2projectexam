const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginView, meta: { guest: true } },
  { path: '/register', component: RegisterView, meta: { guest: true } },
  { path: '/admin', component: AdminDashboard, meta: { role: 'admin' } },
  { path: '/examiner', component: ExaminerDashboard, meta: { role: 'examiner' } },
  { path: '/student', component: StudentDashboard, meta: { role: 'student' } },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
];

const router = VueRouter.createRouter({
  history: VueRouter.createWebHashHistory(),
  routes,
});

const HOME = { admin: '/admin', examiner: '/examiner', student: '/student' };

// Role-based route guard (server enforces the real check; this is UX only)
router.beforeEach((to) => {
  if (to.meta.guest) return authStore.isLoggedIn ? HOME[authStore.role] : true;
  if (to.meta.role) {
    if (!authStore.isLoggedIn) return '/login';
    if (authStore.role !== to.meta.role) return HOME[authStore.role];
  }
  return true;
});
