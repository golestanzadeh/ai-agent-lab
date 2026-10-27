(() => {
  const form = document.getElementById('empty-case-preview-form');
  const status = document.getElementById('empty-case-preview-result');
  if (!form || !status) return;
  const confirmButton = document.createElement('button');
  confirmButton.type = 'button';
  confirmButton.hidden = true;
  confirmButton.textContent = document.documentElement.lang === 'fa-IR'
    ? '\u062a\u0623\u06cc\u06cc\u062f \u0648 \u062d\u0630\u0641 \u0646\u0647\u0627\u06cc\u06cc \u067e\u0631\u0648\u0646\u062f\u0647'
    : 'Endg?ltig best?tigen und l?schen';
  form.after(confirmButton);
  confirmButton.addEventListener('click', async () => {
    const fa = document.documentElement.lang === 'fa-IR';
    const caseId = form.elements.case_id.value;
    const message = fa
      ? `\u0622\u06cc\u0627 \u062d\u0630\u0641 \u067e\u0631\u0648\u0646\u062f\u0647 ${caseId} \u0631\u0627 \u062a\u0623\u06cc\u06cc\u062f \u0645\u06cc\u200c\u06a9\u0646\u06cc\u062f\u061f \u067e\u0648\u0634\u0647 \u0628\u0647 \u0633\u0637\u0644 \u0632\u0628\u0627\u0644\u0647 Google Drive \u0645\u0646\u062a\u0642\u0644 \u0645\u06cc\u200c\u0634\u0648\u062f.`
      : `Fall ${caseId} wirklich l?schen? Der Ordner wird in den Google-Drive-Papierkorb verschoben.`;
    if (!window.confirm(message)) return;
    confirmButton.disabled = true;
    const payload = new FormData(form);
    payload.set('confirmation', caseId);
    try {
      const response = await fetch('/cases/delete/confirm', {
        method: 'POST', body: payload, credentials: 'same-origin',
        headers: {'Accept':'application/json'}
      });
      const result = await response.json();
      if (response.ok && result.deleted && result.database_deleted && result.drive_trashed) {
        status.textContent = fa
          ? '\u062f\u06cc\u062a\u0627\u0628\u06cc\u0633: \u062d\u0630\u0641 \u0634\u062f. Google Drive: \u0628\u0647 \u0633\u0637\u0644 \u0632\u0628\u0627\u0644\u0647 \u0645\u0646\u062a\u0642\u0644 \u0634\u062f.'
          : 'SQLite: gel?scht. Google Drive: in den Papierkorb verschoben.';
        confirmButton.hidden = true;
        setTimeout(() => window.location.assign('/?tab=cases&lang=' + encodeURIComponent(document.documentElement.lang)), 2500);
      } else {
        status.textContent = fa
          ? '\u062d\u0630\u0641 \u062a\u0623\u06cc\u06cc\u062f \u0646\u0634\u062f. \u0647\u0631 \u062f\u0648 \u0645\u0646\u0628\u0639 \u0628\u0627\u06cc\u062f \u0628\u0631\u0631\u0633\u06cc \u0634\u0648\u0646\u062f.'
          : 'L?schung nicht best?tigt. Beide Speicherorte m?ssen gepr?ft werden.';
      }
    } catch (_) {
      status.textContent = fa ? '\u062e\u0637\u0627 \u062f\u0631 \u062d\u0630\u0641\u061b \u0648\u0636\u0639\u06cc\u062a \u0628\u0627\u06cc\u062f \u0628\u0631\u0631\u0633\u06cc \u0634\u0648\u062f.' : 'Fehler; L?schstatus pr?fen.';
    }
    confirmButton.hidden = true;
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    confirmButton.hidden = true;
    confirmButton.disabled = false;
    const fa = document.documentElement.lang === 'fa-IR';
    status.textContent = fa ? '\u062f\u0631 \u062d\u0627\u0644 \u0628\u0631\u0631\u0633\u06cc...' : 'Pr?fung l?uft...';
    try {
      const response = await fetch(form.action, {method:'POST', body:new FormData(form), headers:{'Accept':'application/json'}, credentials:'same-origin'});
      const result = await response.json();
      confirmButton.hidden = !(response.ok && result.ready && result.deletion_enabled);
      status.textContent = response.ok && result.ready
        ? (fa ? '\u062f\u06cc\u062a\u0627\u0628\u06cc\u0633: \u0622\u0645\u0627\u062f\u0647. Google Drive: \u0622\u0645\u0627\u062f\u0647. \u062f\u06a9\u0645\u0647 \u062d\u0630\u0641 \u0646\u0647\u0627\u06cc\u06cc \u0641\u0639\u0627\u0644 \u0627\u0633\u062a.' : 'SQLite: bereit. Google Drive: bereit. Endg?ltige L?schung verf?gbar.')
        : (fa ? '\u0622\u0645\u0627\u062f\u06af\u06cc \u062d\u0630\u0641 \u062a\u0623\u06cc\u06cc\u062f \u0646\u0634\u062f. \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062d\u0630\u0641 \u0646\u0634\u062f.' : 'L?schbereitschaft nicht best?tigt; nichts gel?scht.');
    } catch (_) {
      status.textContent = fa ? '\u062e\u0637\u0627 \u062f\u0631 \u0628\u0631\u0631\u0633\u06cc\u061b \u0686\u06cc\u0632\u06cc \u062d\u0630\u0641 \u0646\u0634\u062f.' : 'Pr?ffehler; nichts gel?scht.';
    }
  });
})();
