const App = {
  components: { NavBar },
  template: `<div><NavBar /><router-view /></div>`,
};

const app = Vue.createApp(App);
app.component('ModalBox', ModalBox);
app.config.globalProperties.$badge = badge;  
app.config.globalProperties.$fmt = fmt;
app.use(router).mount('#app');
