const STATUS_COLORS = {
  Active: 'success', Inactive: 'secondary',
  Approved: 'success', Pending: 'warning', Deactivated: 'secondary',
  Draft: 'secondary', 'Slot Creation': 'info', 'Booking Open': 'primary', Closed: 'dark', Completed: 'success',
  Available: 'success', Full: 'danger', Cancelled: 'secondary', Booked: 'primary',
};
function badge(status) { return 'badge bg-' + (STATUS_COLORS[status] || 'secondary'); }
function fmt(dt) { return dt ? dt.replace('T', ' ') : '-'; }
