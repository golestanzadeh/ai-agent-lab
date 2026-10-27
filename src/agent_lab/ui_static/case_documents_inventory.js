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
          const view = document.createElement('a');
          view.textContent = fa ? "?????" : 'Anzeigen';
          const params = new URLSearchParams({
            case_id: panel.dataset.caseId,
            tax_year: panel.dataset.taxYear,
            document_id: file.id
          });
          view.href = '/cases/documents/view?' + params.toString();
          view.target = '_blank';
          view.rel = 'noopener noreferrer';
          view.style.marginInlineStart = '1rem';
          item.appendChild(view);
          const remove = document.createElement('button');
          remove.type = 'button';
          remove.textContent = fa ? "???" : 'L?schen';
          remove.style.marginInlineStart = '0.5rem';
          remove.addEventListener('click', async () => {
            const question = fa ? "??? ???? ?? ??? ????? Google Drive ????? ????" :
              'Dokument in den Google Drive-Papierkorb verschieben?';
            if (!window.confirm(question)) return;
            remove.disabled = true;
            try {
              const body = new FormData();
              body.set('case_id', panel.dataset.caseId);
              body.set('tax_year', panel.dataset.taxYear);
              body.set('document_id', file.id);
              const response = await fetch('/cases/documents/delete', {
                method: 'POST', body, credentials: 'same-origin'
              });
              const data = await response.json();
              if (!response.ok || !data.deleted || data.document_id !== file.id)
                throw Error('delete');
              await load();
            } catch (_) {
              window.alert(fa ? "??? ????? ???. ???? ?????? ???? ?? ????? ?? ??????? ????? ???." :
                'L?schen fehlgeschlagen. Bitte Dokumentstatus pr?fen.');
              remove.disabled = false;
            }
          });
          item.appendChild(remove);
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
  const form = document.getElementById('case-documents-upload');
  const result = document.getElementById('case-documents-upload-result');
  if (form && result) {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const submit = form.querySelector('button[type="submit"]');
      const file = form.querySelector('input[type="file"]').files[0];
      if (!file || file.size < 1 || file.size > 20 * 1024 * 1024) {
        result.textContent = fa ? 'بارگذاری انجام نشد. نام فایل تکراری، نوع فایل نامعتبر یا خطای اتصال را بررسی کنید.' : 'Ung?ltige Datei oder Gr??e.';
        return;
      }
      submit.disabled = true;
      result.textContent = fa ? 'در حال بارگذاری...' : 'Datei wird hochgeladen...';
      try {
        const response = await fetch('/cases/documents/upload', {
          method: 'POST', body: new FormData(form), credentials: 'same-origin',
          headers: {Accept: 'application/json'}
        });
        const data = await response.json();
        if (!response.ok || !data.uploaded || data.case_id !== panel.dataset.caseId ||
            Number(data.tax_year) !== Number(panel.dataset.taxYear)) throw Error('upload');
        result.textContent = fa ? 'مدرک با موفقیت اضافه شد.' : 'Dokument erfolgreich hochgeladen.';
        form.reset();
        await load();
      } catch (_) {
        result.textContent = fa ? 'بارگذاری انجام نشد. نام فایل تکراری، نوع فایل نامعتبر یا خطای اتصال را بررسی کنید.' : 'Upload fehlgeschlagen. Datei oder Verbindung pr?fen.';
      } finally {
        submit.disabled = false;
      }
    });
  }
  button.addEventListener('click', load);
  load();
})();