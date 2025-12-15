(function () {
  const KEY = 'ageVerified';
  const DAYS = 30;

  function isVerified() {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return false;
      const obj = JSON.parse(raw);
      const ts = obj?.ts || 0;
      return Date.now() < ts + DAYS * 24 * 60 * 60 * 1000;
    } catch {
      return false;
    }
  }

  function setVerified() {
    localStorage.setItem(KEY, JSON.stringify({ ts: Date.now() }));
  }

  function showModal() {
    const modal = document.getElementById('age-gate');
    if (!modal) return;
    modal.classList.add('show');
    document.documentElement.style.overflow = 'hidden';
    const yes = document.getElementById('ag-yes');
    yes?.focus();
  }

  function hideModal() {
    const modal = document.getElementById('age-gate');
    if (!modal) return;
    modal.classList.remove('show');
    document.documentElement.style.overflow = '';
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (isVerified()) return;
    showModal();

    document.getElementById('ag-yes')?.addEventListener('click', function () {
      setVerified();
      hideModal();
    });

    document.getElementById('ag-no')?.addEventListener('click', function () {
      alert('No puedes acceder si no eres mayor de edad.');
      window.location.href = 'about:blank';
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isVerified()) hideModal();
    });
  });
})();