(() => {
  const form = document.getElementById('empty-case-preview-form');
  if (!form) return;
  const status = document.getElementById('empty-case-preview-result');
  const manualStatus = document.getElementById('case-backup-manual-result');
  const manual = document.getElementById('case-backup-manual');
  const backup = document.getElementById('case-backup-predelete');
  const remove = document.getElementById('case-backup-delete');
  const fa = document.documentElement.lang === 'fa-IR';
  const label = (f, d) => fa ? f : d;
  let token = null, busy = false;
  const caseId = form.elements.case_id.value;
  const hide = () => { token = null; backup.hidden = true; remove.hidden = true; };
  async function send(path, extra = {}) {
    const data = new FormData(form);
    Object.entries(extra).forEach(([k, v]) => data.set(k, v));
    const response = await fetch(path, {method:'POST',body:data,credentials:'same-origin',headers:{'Accept':'application/json'}});
    const payload = await response.json();
    if (!response.ok) throw Error(payload.reason || 'HTTP ' + response.status);
    return payload;
  }
  async function check() {
    hide();
    status.textContent = label('در حال بررسی آمادگی حذف...', 'Löschbereitschaft wird geprüft...');
    try {
      const result = await send('/cases/backup/readiness');
      if (result.needs_backup) {
        backup.hidden = false;
        status.textContent = label('پرونده دارای مدرک است. ابتدا پشتیبان تأییدشده ایجاد کنید.', 'Dokumente vorhanden. Zuerst verifiziertes Backup erstellen.');
      } else if (result.ready && result.deletion_enabled && result.token) {
        token = result.token;
        remove.hidden = false;
        status.textContent = label('آمادگی تأیید شد. حذف فقط با تأیید نهایی شما انجام می‌شود.', 'Bereitschaft bestätigt. Löschen erfordert Ihre Bestätigung.');
      } else {
        status.textContent = label('حذف مجاز نیست.', 'Löschen nicht freigegeben.');
      }
    } catch (e) { status.textContent = label('بررسی ناموفق: ', 'Prüfung fehlgeschlagen: ') + e.message; }
  }
  form.addEventListener('submit', async e => { e.preventDefault(); if (busy) return; busy = true; try { await check(); } finally { busy = false; } });
  async function create(trigger) {
    if (busy) return;
    const message = trigger === 'MANUAL'
      ? label('برای پرونده ' + caseId + ' پشتیبان مستقل ایجاد شود؟', 'Eigenständiges Backup für ' + caseId + ' erstellen?')
      : label('پشتیبان تأییدشده برای حذف پرونده ' + caseId + ' ایجاد شود؟', 'Verifiziertes Backup vor Löschung für ' + caseId + ' erstellen?');
    if (!confirm(message)) return;
    busy = true; hide();
    const target = trigger === 'MANUAL' ? manualStatus : status;
    target.textContent = label('در حال ایجاد و تأیید پشتیبان...', 'Backup wird erstellt und geprüft...');
    try {
      const result = await send('/cases/backup/create', {trigger});
      if (!result.verified) throw Error('Backup not verified');
      target.textContent = label('پشتیبان تأیید شد: ', 'Backup verifiziert: ') + result.backup_id;
      if (trigger === 'PRE_DELETE') await check();
    } catch (e) { target.textContent = label('پشتیبان‌گیری ناموفق: ', 'Backup fehlgeschlagen: ') + e.message; }
    finally { busy = false; }
  }
  manual.addEventListener('click', () => create('MANUAL'));
  backup.addEventListener('click', () => create('PRE_DELETE'));
  remove.addEventListener('click', async () => {
    if (!token || busy) return;
    if (!confirm(label('حذف واقعی پرونده ' + caseId + ' و انتقال مدارک به Trash را تأیید می‌کنید؟', 'Fall ' + caseId + ' und Dokumente wirklich in den Papierkorb verschieben?'))) return;
    busy = true; const selected = token; hide();
    status.textContent = label('در حال حذف...', 'Löschung läuft...');
    try {
      const result = await send('/cases/backup/delete-confirm', {token:selected,confirmation:caseId});
      if (!result.deleted || !result.database_deleted || !result.drive_trashed) throw Error('Deletion not verified');
      status.textContent = label('حذف در SQLite و Google Drive تأیید شد.', 'Löschung in SQLite und Google Drive bestätigt.');
      setTimeout(() => location.assign('/?tab=cases&lang=' + encodeURIComponent(document.documentElement.lang)), 1500);
    } catch (e) { status.textContent = label('حذف کامل تأیید نشد. وضعیت را بررسی کنید: ', 'Löschung nicht vollständig bestätigt: ') + e.message; }
    finally { busy = false; }
  });
})();