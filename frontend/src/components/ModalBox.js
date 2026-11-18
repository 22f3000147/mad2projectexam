const ModalBox = {
  props: { title: String, show: Boolean, size: { type: String, default: '' } },
  emits: ['close'],
  template: `
  <div v-if="show">
    <div class="modal-backdrop fade show"></div>
    <div class="modal fade show d-block" tabindex="-1" style="overflow-y:auto" @click.self="$emit('close')">
      <div class="modal-dialog" :class="size">
        <div class="modal-content">
          <div class="modal-header py-2">
            <h5 class="modal-title">{{ title }}</h5>
            <button type="button" class="btn-close" @click="$emit('close')"></button>
          </div>
          <div class="modal-body"><slot /></div>
          <div class="modal-footer py-2" v-if="$slots.footer"><slot name="footer" /></div>
        </div>
      </div>
    </div>
  </div>`,
};
