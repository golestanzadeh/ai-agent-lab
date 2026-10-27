(() => {
  'use strict';
  const panel = document.getElementById('case-documents-list');
  const button = document.getElementById('case-documents-refresh');
  if (!panel || !button) return;
  const fa = panel.dataset.lang === 'fa-IR';
  const load = async () => {
    button.disabled = true;
    panel.textContent = fa ? '\u062f\u0631 \u062d\u0627\u0644 \u062f\u0631\u06cc\u0627\u0641\u062a \u0645\u062f\u0627\u0631\u06a9...' : 'Dokumente werden geladen...';
    try {
      const params = new URLSearchParams({
        case_id: panel.dataset.caseId, tax_year: panel.dataset.taxYear
      });
      const response = await fetch('/cases/documents/inventory?' + params.toString(), {
        credentials: 'same-origin', headers: {Accept: 'application/json'}
      });
      const data = await response.json();
      if (!response.ok || !data.ready || data.case_id !== panel.dataset.caseId ||
          Number(data.tax_year) !== Number(panel.dataset.taxYear)) throw Error('scope');
      panel.replaceChildren();
      if (!data.files.length) {
        panel.textContent = fa ? '\u0647\u0646\u0648\u0632 \u0645\u062f\u0631\u06a9\u06cc \u0628\u0631\u0627\u06cc \u0627\u06cc\u0646 \u067e\u0631\u0648\u0646\u062f\u0647 \u0648\u062c\u0648\u062f \u0646\u062f\u0627\u0631\u062f.' : 'Noch keine Dokumente f\u00fcr diesen Fall.';
      } else {
        const list = document.createElement('ul');
        for (const file of data.files) {
          const item = document.createElement('li');
          item.textContent = file.name;
          list.appendChild(item);
        }
        panel.appendChild(list);
      }
    } catch (_) {
      panel.textContent = fa ? '\u0641\u0647\u0631\u0633\u062a \u0645\u062f\u0627\u0631\u06a9 \u062f\u0631 \u062f\u0633\u062a\u0631\u0633 \u0646\u06cc\u0633\u062a. \u0647\u06cc\u0686 \u062a\u063a\u06cc\u06cc\u0631\u06cc \u0627\u0646\u062c\u0627\u0645 \u0646\u0634\u062f.' : 'Dokumentenliste nicht verf\u00fcgbar. Keine \u00c4nderungen.';
    } finally {
      button.disabled = false;
    }
  };
  button.addEventListener('click', load);
  load();
})();