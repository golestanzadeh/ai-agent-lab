(() => {
  const root = document.querySelector('.family-workspace');
  if (!root) return;
  const fa = root.dataset.lang === 'fa-IR';
  const status = root.querySelector('#family-status');
  const people = root.querySelector('#family-people');
  const form = root.querySelector('#family-editor');
  const add = root.querySelector('#family-add');
  const recover = root.querySelector('#family-recover');
  let recovery = null;
  let pendingWork = [];
  const pendingBox = root.querySelector("#family-mutation-pending");
  const relationships = root.querySelector('#family-relationships');
  const relationshipForm = root.querySelector('#family-relationship-form');
  const endpoint = '/family/persons?' + new URLSearchParams({case_id: root.dataset.caseId,
    tax_year: root.dataset.taxYear, run_id: root.dataset.runId});
  let action = 'create';
  let busy = false;
  const labels = {
    PRIMARY_TAXPAYER: fa ? 'مؤدی اصلی' : 'Steuerpflichtige Person',
    SPOUSE_OR_PARTNER: fa ? 'همسر' : 'Ehepartner/in',
    CHILD: fa ? 'فرزند' : 'Kind',
    OTHER_DEPENDENT_OR_RELEVANT_PERSON: fa ? 'شخص مرتبط دیگر' : 'Weitere Person'
  };
  function text(tag, value) {
    const element = document.createElement(tag);
    element.textContent = value;
    return element;
  }
  function unavailable() {
    add.disabled = true;
    form.hidden = true;
    relationshipForm.hidden = true;
    people.replaceChildren();
    relationships.replaceChildren();
    status.textContent = fa
      ? 'خواندن یا ذخیره ممکن نشد. اتصال مجاز Identity، پرونده/سال/Run و شواهد مالک باید معتبر باشند. هیچ ثبت موفقی تأیید نشده است.'
      : 'Lesen oder Speichern fehlgeschlagen. Identity, Fall/Jahr/Run und Eigentümerbelege müssen autorisiert sein. Keine erfolgreiche Speicherung bestätigt.';
  }
  function open(person) {
    action = person ? 'correct' : 'create';
    form.reset();
    root.querySelector("#family-form-title").textContent=person ? (fa ? "اصلاح مشخصات شخص" : "Person korrigieren") : (fa ? "افزودن شخص" : "Person hinzufügen");
    form.hidden = false;
    form.elements.namedItem('role').disabled = !!person;
    if (person) {
      const values = {...person.attributes, person_id: person.person_id, role: person.role};
      for (const [key, value] of Object.entries(values)) {
        const field = form.elements.namedItem(key);
        if (field) field.value = value;
      }
    }
    form.querySelector('input[name="first_name"]').focus();
  }
  async function loadPending() {
    const response = await fetch(endpoint.replace('/family/persons?', '/family/pending?'), {cache:'no-store', credentials:'same-origin'});
    if (!response.ok) return;
    const data = await response.json();
    if (!Array.isArray(data.pending)) throw new Error('Invalid pending work');
    pendingWork = data.pending;
    pendingBox.replaceChildren();
    for (const work of pendingWork) {
      const button = text('button', fa ? 'تکمیل عملیات قبلی با همان مجوز و شناسه' : 'Vorherigen Vorgang mit gleicher Autorisierung abschließen');
      button.type = 'button';
      button.addEventListener('click', async () => {
        if (busy) return;
        busy = true; button.disabled = true;
        try {
          const reply = await fetch(endpoint.replace('/family/persons?', '/family/persons/recover?'), {
            method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({workflow_id:work.workflow_id})});
          if (!reply.ok) throw new Error('Original recovery remains blocked');
          await loadPending(); await load();
        } catch (_) {
          status.textContent = fa ? 'بازیابی عملیات اصلی هنوز نیازمند مجوز معتبر یا تطبیق شواهد است. ثبت جدید را تکرار نکنید.'
            : 'Originalvorgang benötigt gültige Autorisierung oder Belegabgleich. Keine neue Registrierung starten.';
        } finally {busy = false; button.disabled = false;}
      });
      pendingBox.append(button);
    }
    if (pendingWork.length) add.disabled = true;
  }
  async function load(resume = false) {
    recover.hidden = true;
    const response = await fetch(endpoint + (resume && recovery ? "&recovery=" + encodeURIComponent(recovery) : ""), {cache: 'no-store', credentials: 'same-origin'});
    if (!response.ok) {
      let missingRuntime = response.headers.get('X-Family-Blocker') === 'FAMILY_RUNTIME_BINDING_REQUIRED';
      if (response.status === 503 && !missingRuntime) {
        try { missingRuntime = (await response.json()).detail === 'FAMILY_AUTHORIZED_RUNTIME_UNAVAILABLE'; }
        catch (_) { /* Keep an unknown failure fail-closed. */ }
      }
      if (response.status === 503 && missingRuntime) {
        unavailable();
        status.textContent = fa
          ? 'ثبت و خواندن اشخاص غیرفعال است: اتصال تأییدشدهٔ هویت و مجوز مالک به برنامه متصل نشده است. ابتدا binding عملیاتی و تأییدهای امنیتی همان استقرار باید تکمیل شوند.'
          : 'Personen sind nicht verfügbar: Die freigegebene Identity-Verbindung mit Eigentümerautorisierung ist nicht angebunden. Zuerst sind die Betriebsbindung und Sicherheitsfreigaben dieser Installation erforderlich.';
        return;
      }
      if (response.status === 409) {
        const error = await response.json();
        if (error.detail === 'FAMILY_READ_RECONCILIATION_REQUIRED' && typeof error.transaction_id === 'string') {
          unavailable();
          recovery = error.transaction_id;
          recover.hidden = false;
          status.textContent = fa ? 'خواندن به زمان بیشتری برای تأیید نیاز دارد. با دکمه زیر همان درخواست را تکمیل کنید؛ ثبت شخص را تکرار نکنید.'
            : 'Lesebestätigung benötigt mehr Zeit. Vorherigen Lesevorgang unten abschließen; Person nicht erneut speichern.';
          return;
        }
      }
      throw new Error('Family unavailable');
    }
    recovery = null;
    const data = await response.json();
    if (data.case_id !== root.dataset.caseId || String(data.tax_year) !== root.dataset.taxYear
        || data.run_id !== root.dataset.runId || !Array.isArray(data.people)
        || !Array.isArray(data.relationships)) throw new Error('Family scope mismatch');
    people.replaceChildren();
    for (const person of data.people) {
      const card = text('article', '');
      card.className = 'family-person';
      const info = text('div', '');
      info.append(text('strong', person.name || person.person_id),
        text('small', person.person_id + ' · ' + (labels[person.role] || person.role)),
        text('small', person.attributes.birth_date || ''));
      card.append(info);
      if (data.writes_available && !pendingWork.length) {
        const edit = text('button', fa ? 'اصلاح با حفظ شناسه' : 'Mit gleicher ID korrigieren');
        edit.type = 'button';
        edit.addEventListener('click', () => open(person));
        card.append(edit);
      }
      people.append(card);
    }
    if (!data.people.length) people.append(text('p', fa ? 'شخص مرتبطی ثبت نشده است.' : 'Keine zugeordnete Person.'));
    relationships.replaceChildren();
    for (const relation of data.relationships) {
      relationships.append(text('p', (fa ? 'ازدواج: ' : 'Ehe: ') + relation.subject_a_id + ' ↔ '
        + relation.subject_b_id + (fa ? ' · اعتبار در پرونده از ' : ' · im Fall gültig ab ') + relation.valid_from));
    }
    add.disabled = !data.writes_available || !!pendingWork.length;
    relationshipForm.hidden = !data.relationship_writes_available;
    status.textContent = data.writes_available
      ? (fa ? 'اطلاعات پایدار از مسیر Kernel/Identity خوانده شد. هر تغییر به شواهد و مجوز مستقل نیاز دارد.'
        : 'Dauerhafte Daten über Kernel/Identity gelesen. Jede Änderung benötigt Belege und Autorisierung.')
      : (fa ? 'خواندن پایدار فعال است؛ ثبت و اصلاح تا اتصال شواهد و مجوز معتبر غیرفعال است.'
        : 'Dauerhaftes Lesen aktiv; Schreiben bis zur Beleg- und Autorisierungsbindung gesperrt.');
  }
  async function save(command, values) {
    if (busy) return;
    busy = true;
    root.querySelectorAll('button[type="submit"]').forEach(button => button.disabled = true);
    try {
      const body = {action: command, values};
      const canonical = JSON.stringify(body, Object.keys({...body, ...values}).sort());
      const response = await fetch(endpoint, {method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json'}, body: canonical});
      if (!response.ok) throw new Error('Family authorization or reconciliation required');
      form.hidden = true;
      await loadPending(); await load();
    } catch (_) { unavailable(); await loadPending().catch(() => {}); }
    finally {
      busy = false;
      root.querySelectorAll('button[type="submit"]').forEach(button => button.disabled = false);
    }
  }
  recover.addEventListener('click', () => load(true).catch(unavailable));
  add.addEventListener('click', () => open(null));
  root.querySelector('#family-cancel').addEventListener('click', () => { form.hidden = true; });
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const values = Object.fromEntries(new FormData(form));
    delete values.church_tax;
    if (!values.person_id) delete values.person_id;
    if (!values.tax_id) delete values.tax_id;
    save(action, values);
  });
  relationshipForm.addEventListener('submit', event => {
    event.preventDefault();
    if (relationshipForm.reportValidity()) save('relationship', Object.fromEntries(new FormData(relationshipForm)));
  });
  loadPending().then(() => load()).catch(unavailable);
})();
