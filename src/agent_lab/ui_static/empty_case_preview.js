(() => {
  const form = document.getElementById('empty-case-preview-form');
  const status = document.getElementById('empty-case-preview-result');
  if (!form || !status) return;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const fa = document.documentElement.lang === 'fa-IR';
    status.textContent = fa ? 'در حال بررسی...' : 'Prüfung l?uft...';
    try {
      const response = await fetch(form.action, {method:'POST', body:new FormData(form), headers:{'Accept':'application/json'}, credentials:'same-origin'});
      const result = await response.json();
      status.textContent = response.ok && result.ready
        ? (fa ? 'دیتابیس: آماده حذف. مخزن مدارک: آماده حذف. حذف واقعی هنوز فعال نیست.' : 'SQLite: bereit. Dokumentenspeicher: bereit. Löschen ist noch nicht aktiviert.')
        : (fa ? 'آمادگی حذف تأیید نشد؛ هیچ داده‌ای حذف نشد.' : 'Löschbereitschaft nicht bestätigt; keine Daten gelöscht.');
    } catch (_) {
      status.textContent = fa ? 'خطا در بررسی؛ هیچ داده‌ای حذف نشد.' : 'Pr?ffehler; keine Daten gelöscht.';
    }
  });
})();
