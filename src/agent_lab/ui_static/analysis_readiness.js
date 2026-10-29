(() => {
  'use strict';
  const panel = document.getElementById('analysis-readiness');
  if (!panel) return;
  const details = document.getElementById('analysis-readiness-details');
  const status = document.getElementById('analysis-readiness-state');
  const fa = panel.dataset.lang === 'fa-IR';
  const params = new URLSearchParams({case_id: panel.dataset.caseId, tax_year: panel.dataset.taxYear});
  fetch('/cases/analysis/readiness?' + params, {credentials:'same-origin',cache:'no-store'})
    .then(async response => {if (!response.ok) throw Error('PREFLIGHT_FAILED'); return response.json();})
    .then(data => {
      if (!data.inventory_verified || data.case_id !== panel.dataset.caseId || String(data.tax_year) !== panel.dataset.taxYear) throw Error('SCOPE_MISMATCH');
      const types = data.document_types;
      if (!types || typeof types !== 'object' || Array.isArray(types) ||
          Object.values(types).some(n => !Number.isInteger(n) || n < 1) ||
          Object.values(types).reduce((sum,n) => sum+n,0) !== data.documents_count) throw Error('INVALID_COUNTS');
      const lines = [fa ? `مدارک: ${data.documents_count}` : `Dokumente: ${data.documents_count}`];
      for (const [kind,n] of Object.entries(types).sort(([a],[b]) => a.localeCompare(b))) lines.push(`${kind}: ${n}`);
      lines.push(fa ? `Kernel: ${data.kernel_ready ? 'متصل' : 'آماده نیست'}` : `Kernel: ${data.kernel_ready ? 'verbunden' : 'nicht bereit'}`);
      lines.push(fa ? `Gemini: ${data.gemini_ready ? 'کلید در دسترس است' : 'کلید در دسترس نیست'}` : `Gemini: ${data.gemini_ready ? 'Schlüssel verfügbar' : 'Schlüssel fehlt'}`);
      details.replaceChildren(...lines.map(line => {const p=document.createElement('p');p.textContent=line;return p;}));
      if (!panel.dataset.executionStarted) status.textContent = data.analysis_launch_available
        ? (fa ? 'آماده شروع استخراج اسناد PDF' : 'Bereit zur PDF-Extraktion')
        : (fa ? 'شروع تحلیل در حال حاضر ممکن نیست' : 'Analysestart derzeit nicht verfügbar');
    })
    .catch(() => {if (!panel.dataset.executionStarted) status.textContent = fa ? 'بررسی آمادگی ناموفق بود' : 'Bereitschaftsprüfung fehlgeschlagen';});
})();
