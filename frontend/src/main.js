const App = {
  components: { NavBar },
  template: `<div><NavBar /><router-view /></div>`,
};
Vue.createApp(App).use(router).mount('#app');
