(() => {
  'use strict';
  const panel = document.getElementById('analysis-readiness');
  if (!panel) return;
  const state = document.getElementById('analysis-readiness-state');
  const details = document.getElementById('analysis-readiness-details');
  const fa = panel.dataset.lang === 'fa-IR';
  const params = new URLSearchParams({case_id: panel.dataset.caseId, tax_year: panel.dataset.taxYear});
  fetch('/cases/analysis/readiness?' + params, {credentials: 'same-origin', cache: 'no-store'})
    .then(async response => { if (!response.ok) throw new Error('PREFLIGHT_FAILED'); return response.json(); })
    .then(data => {
      if (!data.inventory_verified || data.case_id !== panel.dataset.caseId || String(data.tax_year) !== panel.dataset.taxYear) throw new Error('SCOPE_MISMATCH');
      state.textContent = fa ? 'موجودی مدارک تأیید شد؛ اجرای تحلیل هنوز آماده نیست.' : 'Dokumentenbestand bestätigt; Analysestart noch nicht bereit.';
      const types = data.document_types;
      if (!types || typeof types !== 'object' || Array.isArray(types) ||
          Object.values(types).some(count => !Number.isInteger(count) || count < 1) ||
          Object.values(types).reduce((total, count) => total + count, 0) !== data.documents_count) {
        throw new Error('INVALID_INVENTORY_COUNTS');
      }
      const lines = [fa ? `مدارک: ${data.documents_count}` : `Dokumente: ${data.documents_count}`];
      if (data.documents_count === 0) {
        lines.push(fa ? 'هنوز مدرکی برای این پرونده بارگذاری نشده است.' : 'Für diesen Fall wurden noch keine Dokumente hochgeladen.');
      } else {
        for (const [type, count] of Object.entries(types).sort(([a], [b]) => a.localeCompare(b))) {
          lines.push(`${type}: ${count}`);
        }
      }
      lines.push(fa ? 'Kernel: اتصال اجرای واقعی برقرار نیست' : 'Kernel: Laufzeit nicht angebunden');
      lines.push(fa ? 'Gemini: آمادگی اجرایی تأیید نشده' : 'Gemini: Bereitschaft nicht bestätigt');
      details.replaceChildren(...lines.map(line => { const p = document.createElement('p'); p.textContent = line; return p; }));
    })
    .catch(() => {
      state.textContent = fa ? 'بررسی آمادگی ناموفق بود؛ اجرای تحلیل مسدود است.' : 'Bereitschaftsprüfung fehlgeschlagen; Analysestart gesperrt.';
      details.replaceChildren();
    });
})();
