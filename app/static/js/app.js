document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('[data-sidebar]');
  const toggle = document.querySelector('[data-sidebar-toggle]');

  if (sidebar && toggle) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('is-open');
    });
  }

  document.querySelectorAll('form[data-clean-empty-query="true"]').forEach((form) => {
    form.addEventListener('submit', () => {
      form.querySelectorAll('input[name], select[name], textarea[name]').forEach((field) => {
        if (!field.value) {
          field.disabled = true;
        }
      });
    });
  });
});
