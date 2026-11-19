/* Local-only progressive enhancement: accessible nav, theme, form confirmations. */
(function () {
  'use strict';
  const root = document.documentElement;
  try { root.dataset.theme = localStorage.getItem('campusvote-theme') === 'dark' ? 'dark' : 'light'; } catch (_) {}
  document.querySelectorAll('.theme-toggle').forEach(button => button.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('campusvote-theme', root.dataset.theme); } catch (_) {}
  }));

  const sidebar = document.getElementById('sidebar');
  const menu = document.getElementById('mobile-menu');
  const scrim = document.getElementById('sidebar-scrim');
  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove('open'); scrim?.classList.remove('visible');
    menu?.setAttribute('aria-expanded', 'false');
  }
  menu?.addEventListener('click', () => {
    const open = !sidebar.classList.contains('open');
    sidebar.classList.toggle('open', open);
    scrim.classList.toggle('visible', open);
    menu.setAttribute('aria-expanded', String(open));
  });
  scrim?.addEventListener('click', closeSidebar);
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape') closeSidebar(); });

  document.querySelectorAll('[data-password-toggle]').forEach(button => button.addEventListener('click', () => {
    const input = document.getElementById(button.dataset.passwordToggle);
    if (!input) return;
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.textContent = show ? 'Hide' : 'Show';
    button.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
  }));
  document.querySelectorAll('[data-confirm]').forEach(form => form.addEventListener('submit', ev => {
    if (!window.confirm(form.dataset.confirm)) ev.preventDefault();
  }));
  document.querySelectorAll('[data-scroll-to]').forEach(button => button.addEventListener('click', () => {
    document.getElementById(button.dataset.scrollTo)?.scrollIntoView({behavior:'smooth',block:'start'});
  }));
  document.querySelectorAll('.toast-dismiss').forEach(button => button.addEventListener('click', () => button.parentElement?.remove()));
  document.querySelectorAll('[data-print-receipt]').forEach(button => button.addEventListener('click', () => window.print()));

  const form = document.getElementById('ballot-form');
  const modal = document.getElementById('vote-modal');
  const submit = document.getElementById('confirm-vote');
  const cancel = document.getElementById('cancel-vote');
  let verified = false;
  if (form && modal && submit && cancel) {
    form.addEventListener('submit', ev => {
      if (verified) return;
      ev.preventDefault();
      const checked = form.querySelector('input[name="candidate_id"]:checked');
      if (!checked) { form.reportValidity(); return; }
      const name = checked.closest('.candidate-select')?.querySelector('.candidate-content>strong')?.textContent || 'your candidate';
      document.getElementById('modal-candidate-name').textContent = 'You selected ' + name + '. Confirm to submit your final ballot.';
      modal.hidden = false;
      cancel.focus();
    });
    function closeModal() { modal.hidden = true; }
    cancel.addEventListener('click', closeModal);
    modal.addEventListener('click', ev => { if (ev.target === modal) closeModal(); });
    document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && !modal.hidden) closeModal(); });
    submit.addEventListener('click', () => { verified = true; submit.disabled = true; form.requestSubmit(); });
  }
}());
