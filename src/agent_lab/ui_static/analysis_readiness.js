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
      const lines = fa
        ? [`مدارک: ${data.documents_count}`, `PDF: ${data.pdf_count}`, `CSV: ${data.csv_count}`, 'Kernel: اتصال اجرای واقعی برقرار نیست', 'Gemini: آمادگی اجرایی تأیید نشده']
        : [`Dokumente: ${data.documents_count}`, `PDF: ${data.pdf_count}`, `CSV: ${data.csv_count}`, 'Kernel: Laufzeit nicht angebunden', 'Gemini: Bereitschaft nicht bestätigt'];
      details.replaceChildren(...lines.map(line => { const p = document.createElement('p'); p.textContent = line; return p; }));
    })
    .catch(() => {
      state.textContent = fa ? 'بررسی آمادگی ناموفق بود؛ اجرای تحلیل مسدود است.' : 'Bereitschaftsprüfung fehlgeschlagen; Analysestart gesperrt.';
      details.replaceChildren();
    });
})();
