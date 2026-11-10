(() => {
  'use strict';
  const panel=document.getElementById('analysis-readiness');
  const button=document.getElementById('analysis-start-real');
  const state=document.getElementById('analysis-readiness-state');
  if(!panel||!button||!state)return;
  const recoveryScript=document.createElement('script');recoveryScript.src='/static/analysis_recovery.js';document.head.append(recoveryScript);
  const fa=panel.dataset.lang==='fa-IR';
  const labels=fa?{QUEUED:'در صف',RUNNING:'در حال تحلیل',HUMAN_REVIEW_REQUIRED:'استخراج‌شده؛ نیازمند بازبینی',FAILED:'ناموفق',RECONCILIATION_REQUIRED:'نیازمند بازیابی بررسی‌شده'}:{QUEUED:'Eingereiht',RUNNING:'Analyse läuft',HUMAN_REVIEW_REQUIRED:'Extrahiert; Prüfung erforderlich',FAILED:'Fehlgeschlagen',RECONCILIATION_REQUIRED:'Abgestimmte Wiederherstellung erforderlich'};
  const params=new URLSearchParams({case_id:panel.dataset.caseId,tax_year:panel.dataset.taxYear});
  const results=document.createElement('section');results.setAttribute('aria-live','polite');panel.append(results);
  const text=(node,value)=>{node.textContent=value;return node;};
  let inventoryTargets=[];
  async function progress(){
    try{
      const r=await fetch('/cases/analysis/progress?'+params,{credentials:'same-origin',cache:'no-store'});
      if(!r.ok)return;
      const p=await r.json();
      if(p.case_id!==panel.dataset.caseId||String(p.tax_year)!==panel.dataset.taxYear)return;
      const nodes=[text(document.createElement('p'),fa?`تکمیل استخراج: ${p.completed} | ناموفق: ${p.failed}`:`Extrahiert: ${p.completed} | Fehlgeschlagen: ${p.failed}`)];
      for(const d of p.documents){
        const section=document.createElement('article');
        section.append(text(document.createElement('h3'),d.filename));
        section.append(text(document.createElement('p'),`${d.document_id} | SHA-256: ${d.sha256}`));
        section.append(text(document.createElement('p'),(labels[d.processing_status]||d.processing_status)+' | '+d.run_id));
        section.append(text(document.createElement('p'),fa?'خروجی پیشنهادی؛ تأیید مالیاتی نشده':'Kandidat; steuerlich nicht akzeptiert'));
        if(d.error_details)section.append(text(document.createElement('p'),d.error_details));
        if(d.extraction_payload){
          const table=document.createElement('table');
          for(const f of d.extraction_payload.fields){
            const row=document.createElement('tr');
            for(const v of [f.name,f.value,String(f.page),f.evidence])row.append(text(document.createElement('td'),v));
            table.append(row);
          }
          section.append(table);
        }
        if(d.previous_valid_result){const previous=document.createElement('details');previous.append(text(document.createElement('summary'),fa?'نتیجهٔ معتبر قبلی محفوظ است':'Vorheriges gültiges Ergebnis bleibt erhalten'));previous.append(text(document.createElement('pre'),JSON.stringify(d.previous_valid_result.extraction_payload||d.previous_valid_result.csv_payload?.summary,null,2)));section.append(previous);}
        if(d.csv_payload)section.append(text(document.createElement('pre'),JSON.stringify({summary:d.csv_payload.summary,credits:d.csv_payload.credits,debits:d.csv_payload.debits,net:d.csv_payload.net,classification_status:d.csv_payload.classification_status,source_category_totals:d.csv_payload.source_category_totals},null,2)));
        section.append(text(document.createElement('p'),d.initiated_via==='DASHBOARD'?(fa?'آغازشده از داشبورد؛ یافته‌ها پذیرفته نشده‌اند':'Im Dashboard gestartet; Befunde nicht akzeptiert'):(fa?'نتیجهٔ تاریخی؛ نحوهٔ آغاز به‌طور مستقل تأیید نشده':'Historisches Ergebnis; Startursprung nicht unabhängig belegt')));
        const action=text(document.createElement('button'),fa?'آنالیز مجدد':'Erneut analysieren');action.type='button';action.disabled=p.active||['QUEUED','RUNNING','RECONCILIATION_REQUIRED'].includes(d.processing_status);
        action.onclick=()=>{if(window.confirm(fa?'یک تلاش جدید فقط برای این سند آغاز شود؟ نتیجهٔ قبلی ممکن است نامطمئن باشد؛ تاریخچه حفظ می‌شود.':'Genau einen neuen Versuch für dieses Dokument starten? Der vorherige Ausgang kann ungewiss sein; die Historie bleibt erhalten.'))send({scope:'DOCUMENT',document_id:d.document_id,execution_intent:'EXPLICIT_RERUN',expected_sha256:d.sha256},action);};section.append(action);
        nodes.push(section);
      }
      for(const o of (p.batch_outcomes||[]).slice(-1)){nodes.push(text(document.createElement('p'),`${o.run_id} | ${fa?'تلاش جدید / استفادهٔ مجدد':'Neue Versuche / wiederverwendet'}: ${o.attempted_this_run??0} / ${o.reused_unchanged??0}`));for(const u of (o.unsupported||[]))nodes.push(text(document.createElement('p'),`${u.filename}: ${fa?'قالب پشتیبانی نمی‌شود':'Format nicht unterstützt'}`));if(o.reconciliation_required?.length)nodes.push(text(document.createElement('p'),fa?'نتیجهٔ قبلی نامطمئن است؛ برای بررسی و یک تلاش تازه، آنالیز مجدد همان سند را انتخاب کنید.':'Vorheriger Ausgang ungewiss; für einen geprüften neuen Versuch das betreffende Dokument erneut analysieren.'));}
      const seen=new Set(p.documents.map(d=>d.document_id));
      for(const f of inventoryTargets)if(!seen.has(f.id)){
        const line=document.createElement('article');line.append(text(document.createElement('h3'),f.name));
        const action=text(document.createElement('button'),fa?'آنالیز':'Analysieren');action.type='button';
        action.disabled=p.active||!['application/pdf','text/csv'].includes(f.mime_type);
        action.onclick=()=>send({scope:'DOCUMENT',document_id:f.id,execution_intent:'NORMAL'},action);
        line.append(action);if(action.disabled&&!p.active)line.append(text(document.createElement('p'),fa?'قالب پشتیبانی نمی‌شود':'Format nicht unterstützt'));nodes.push(line);
      }
      results.replaceChildren(...nodes);
      document.dispatchEvent(new CustomEvent('case-analysis-progress',{detail:p}));
      if(p.active){state.textContent=fa?'استخراج در حال اجرا؛ نتایج هر سند جدا ذخیره می‌شود':'Extraktion läuft; Ergebnisse werden einzeln gespeichert';button.disabled=true;}
      else if(panel.dataset.executionStarted||p.runs.length){panel.dataset.executionStarted='true';state.textContent=fa?'وضعیت پایدار بازیابی شد؛ نتایج نیازمند بازبینی هستند':'Dauerhafter Status geladen; Ergebnisse benötigen Prüfung';}
      button.disabled=p.active;
    }catch(_){button.disabled=true;state.textContent=fa?'بازیابی وضعیت تأییدشده ممکن نیست':'Verifizierter Status nicht verfügbar';}
  }
  fetch('/cases/analysis/readiness?'+params,{credentials:'same-origin',cache:'no-store'}).then(r=>r.json()).then(d=>{
    if(d.inventory_verified===true&&d.analysis_launch_available===true&&d.case_id===panel.dataset.caseId&&String(d.tax_year)===panel.dataset.taxYear){
      inventoryTargets=d.document_targets||[];
      button.disabled=false;button.setAttribute('aria-disabled','false');button.textContent=fa?'آنالیز پرونده':'Fall analysieren';
    }
  }).catch(()=>{});
  const pending=new Map();
  async function send(extra,control){
    const key=JSON.stringify(extra);const requestId=pending.get(key)||crypto.randomUUID();pending.set(key,requestId);
    control.disabled=true;panel.dataset.executionStarted='true';
    try{
      const r=await fetch('/cases/analysis/execute',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({...Object.fromEntries(params),...extra,request_id:requestId})});
      if(!r.ok)throw Error('HTTP_'+r.status);
      const receipt=await r.json();if(receipt.case_id!==panel.dataset.caseId||String(receipt.tax_year)!==panel.dataset.taxYear||!receipt.run_id)throw Error('INVALID_RECEIPT');
      pending.delete(key);state.textContent=(fa?'در صف Kernel؛ هنوز نتیجه نیست: ':'Im Kernel eingereiht; noch kein Ergebnis: ')+receipt.run_id;await progress();
    }catch(e){state.textContent=(fa?'شروع ناموفق؛ وضعیت را بازخوانی کنید: ':'Start fehlgeschlagen; Status neu laden: ')+e.message;control.disabled=false;}
  }
  button.addEventListener('click',()=>{if(!button.disabled)send({scope:'CASE',execution_intent:'NORMAL'},button);});
  progress();setInterval(progress,2500);
})();
