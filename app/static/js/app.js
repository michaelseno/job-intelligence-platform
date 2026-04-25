document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('[data-sidebar]');
  const toggle = document.querySelector('[data-sidebar-toggle]');
  const backdrop = document.querySelector('[data-sidebar-backdrop]');
  const focusableSelector = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';
  let previousFocus = null;

  const closeSidebar = () => {
    if (!sidebar || !toggle) {
      return;
    }

    sidebar.classList.remove('is-open');
    document.body.classList.remove('sidebar-open');
    toggle.setAttribute('aria-expanded', 'false');

    if (window.matchMedia('(max-width: 1023px)').matches && previousFocus instanceof HTMLElement) {
      previousFocus.focus();
    }
  };

  const openSidebar = () => {
    if (!sidebar || !toggle) {
      return;
    }

    previousFocus = document.activeElement;
    sidebar.classList.add('is-open');
    document.body.classList.add('sidebar-open');
    toggle.setAttribute('aria-expanded', 'true');

    const firstFocusable = sidebar.querySelector(focusableSelector);
    if (firstFocusable instanceof HTMLElement) {
      firstFocusable.focus();
    } else {
      sidebar.focus();
    }
  };

  if (sidebar && toggle) {
    toggle.addEventListener('click', () => {
      if (sidebar.classList.contains('is-open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });

    if (backdrop) {
      backdrop.addEventListener('click', closeSidebar);
    }

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && sidebar.classList.contains('is-open')) {
        closeSidebar();
        return;
      }

      if (event.key === 'Tab' && sidebar.classList.contains('is-open') && window.matchMedia('(max-width: 1023px)').matches) {
        const focusable = Array.from(sidebar.querySelectorAll(focusableSelector));
        if (!focusable.length) {
          return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    });

    window.addEventListener('resize', () => {
      if (!window.matchMedia('(max-width: 1023px)').matches) {
        document.body.classList.remove('sidebar-open');
        sidebar.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      }
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
