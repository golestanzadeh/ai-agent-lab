(() => {
  'use strict';
  const panel=document.getElementById('analysis-readiness');
  if(!panel)return;
  const fa=panel.dataset.lang==='fa-IR';
  const scope={case_id:panel.dataset.caseId,tax_year:panel.dataset.taxYear};
  const area=document.createElement('section');area.id='document-recovery';panel.append(area);
  const node=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
  const codes={
    PROVIDER_CONFIGURATION_MISSING:fa?'کلید Gemini در فرایند اجرا تنظیم نشده است؛ پس از اصلاح، یک تلاش جدید را تأیید کنید.':'Der explizite Gemini-Schlüssel fehlt im Prozess. Nach der Konfiguration einen neuen Versuch genehmigen.',
    LEGACY_ERROR_CONTEXT_UNAVAILABLE:fa?'مرحله و traceback خطای قدیمی ذخیره نشده؛ علت قطعی بازیابی نشده است.':'Stufe und Traceback des alten Fehlers wurden nicht gespeichert; Ursache nicht belegt.',
    PROVIDER_OUTCOME_UNCERTAIN:fa?'نتیجهٔ فراخوانی سرویس نامطمئن است؛ تلاش خودکار ممنوع است.':'Der Provider-Ausgang ist ungewiss. Kein automatischer Wiederholungsversuch.',
    AUTHORIZATION_DENIED:fa?'مجوز Kernel رد شد؛ محدوده و Human Gate بررسی شود.':'Kernel-Autorisierung verweigert. Umfang und Human Gate prüfen.',
    DOCUMENT_REJECTED:fa?'هویت یا قالب سند تأیید نشد.':'Dokumentidentität oder Format nicht bestätigt.',
    APPLICATION_ERROR:fa?'خطای برنامه؛ اطلاعات فنی پاک‌سازی‌شده ثبت شده است.':'Anwendungsfehler; bereinigter technischer Kontext gespeichert.'
  };
  function render(p){
    if(p.case_id!==scope.case_id||String(p.tax_year)!==scope.tax_year)return;
    area.replaceChildren();
    for(const d of p.documents.filter(x=>x.diagnostic)){
      const card=document.createElement('article'),diag=d.diagnostic;
      card.append(node('h3',d.filename),node('p',codes[diag.error_code]||codes.APPLICATION_ERROR));
      card.append(node('p',`${diag.error_code} | ${diag.stage} | ${diag.timestamp} | ${diag.run_id}`));
      area.append(card);
    }
    if(p.history.length){const h=document.createElement('details');h.append(node('summary',fa?'تاریخچهٔ تلاش‌های قبلی':'Historie früherer Versuche'));for(const d of p.history)h.append(node('p',`${d.filename} | ${d.processing_status} | ${d.run_id}`));area.append(h);}
  }
  document.addEventListener('case-analysis-progress',e=>render(e.detail));
  fetch('/cases/analysis/progress?'+new URLSearchParams(scope),{cache:'no-store',credentials:'same-origin'}).then(r=>r.ok?r.json():null).then(p=>p&&render(p)).catch(()=>{});
  const verified=document.createElement('section');verified.id='verified-case-results';panel.append(verified);
  fetch('/cases/analysis/verified-results?'+new URLSearchParams(scope),{cache:'no-store',credentials:'same-origin'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(value=>{
    if(value.case_id!==scope.case_id||String(value.tax_year)!==scope.tax_year)throw Error();
    if(!value.result){verified.append(node('p',fa?'نتیجهٔ تجمیعی تأییدشده هنوز وارد نشده است.':'Noch kein verifiziertes Gesamtergebnis importiert.'));return;}
    const p=value.result.payload;
    verified.append(node('h3',fa?'نتایج مستند CSV و محاسبات جزئی':'Belegte CSV-Ergebnisse und Teilberechnungen'));
    verified.append(node('p',fa?'ارقام مستند و راستی‌آزمایی‌شده؛ درآمد مشمول مالیات یا استرداد نهایی نیست.':'Belegte, verifizierte Teilbeträge; kein endgültiges zu versteuerndes Einkommen oder Erstattungsbetrag.'));
    verified.append(node('p',`CSV: ${p.csv.status} | ${p.csv.row_count} | +${p.csv.credits} / -${p.csv.debits} EUR | ${p.csv.net} EUR`));
    const labels={employment_gross_from_this_certificate:fa?'ناخالص گواهی حقوق':'Brutto laut Bescheinigung',employee_expense_allowance_2025:fa?'کسر مقطوع شغلی':'Arbeitnehmer-Pauschbetrag',employment_income_component_using_allowance:fa?'مؤلفهٔ درآمد شغلی؛ نه درآمد مشمول مالیات کل':'Einkünfteanteil aus Arbeit; nicht gesamtes z.v.E.',employee_social_contributions_document_total:fa?'جمع پرداخت‌های بیمه؛ نه کسر قطعی':'Bescheinigte Sozialbeiträge; kein bestätigter Abzug',wage_tax_withheld:fa?'مالیات حقوق کسرشده':'Einbehaltene Lohnsteuer'};
    for(const [k,v] of Object.entries(p.subtotals))if(typeof v==='string')verified.append(node('p',`${labels[k]||k}: ${v} EUR`));
    const conditional=document.createElement('details');conditional.append(node('summary',fa?'ارقام مشروط؛ هنوز پذیرفته نشده':'Bedingte Beträge; noch nicht akzeptiert'));
    const conditionalLabels={school_deduction_if_2025eligibility_and_child_attribution_proved:fa?'شهریه؛ مشروط به شرایط مدرسه و فرزند':'Schulgeld; Schul- und Kindvoraussetzungen offen',section35a_potential_credit_if_year_payment_and_eligibility_proved:fa?'اعتبار خدمات خانه؛ سال و شرایط هنوز باز':'Haushaltsnahe Steuerermäßigung; Jahr und Voraussetzungen offen',total_pension_basic_health_care_if_conditions_hold:fa?'بازنشستگی/درمان/مراقبت؛ برآورد مشروط':'Altersvorsorge/Kranken-/Pflegeversicherung; bedingte Berechnung'};
    for(const [k,v] of Object.entries(p.conditional))conditional.append(node('p',`${conditionalLabels[k]||k}: ${String(v)}`));verified.append(conditional);
    const links=document.createElement('details');links.append(node('summary',(fa?'پیوندهای سند و بانک: ':'Dokument-Bank-Verknüpfungen: ')+p.links.length));
    for(const l of p.links)links.append(node('p',`${l.document_id} | ${l.page} | ${l.row_id} | ${l.amount} EUR`));verified.append(links);
    const spouseLabels={source_months:fa?'ماه‌های سند':'Belegmonate',zv_brutto_year_to_date:fa?'ZV-Brutto تجمعی فیش دسامبر؛ نه ناخالص مالیاتی تأییدشده':'ZV-Brutto kumuliert laut Dezember; kein bestätigtes Steuerbrutto',bank_credits_2025:fa?'جمع واریزهای واقعی بانک':'Summe tatsächlicher Bankgutschriften',bank_payment_count:fa?'تعداد واریزهای واقعی':'Anzahl tatsächlicher Zahlungen',tax_status:fa?'وضعیت مالیاتی؛ هنوز نهایی نیست':'Steuerstatus; noch nicht abschließend'};
    if(p.spouse_payroll){verified.append(node('h4',fa?'شواهد فیش همسر؛ بدون برون‌یابی، نه پذیرش مالیات نهایی':'Gehaltsbelege der Eheperson; ohne Hochrechnung, keine abschließende Steuerakzeptanz'));for(const [k,v] of Object.entries(p.spouse_payroll))verified.append(node('p',`${spouseLabels[k]||k}: ${String(v)}`));}
    verified.append(node('h4',fa?'سؤالات و شواهد باقی‌مانده':'Offene Fragen und Nachweise'));
    for(const q of p.questions)verified.append(node('p',typeof q==='string'?q:q[panel.dataset.lang]));
    verified.append(node('p',value.result.run_id));
  }).catch(()=>verified.append(node('p',fa?'خواندن نتیجهٔ تجمیعیِ تأییدشده ممکن نیست؛ دادهٔ جایگزین نمایش داده نمی‌شود.':'Verifiziertes Gesamtergebnis nicht verfügbar; keine Ersatzdaten.')));
})();
