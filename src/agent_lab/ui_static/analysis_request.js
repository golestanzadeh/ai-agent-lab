(() => {
  'use strict';
  const panel=document.getElementById('analysis-readiness');
  const button=document.getElementById('analysis-start-real');
  const state=document.getElementById('analysis-readiness-state');
  if(!panel||!button||!state)return;
  const fa=panel.dataset.lang==='fa-IR';
  const params=new URLSearchParams({case_id:panel.dataset.caseId,tax_year:panel.dataset.taxYear});
  const results=document.createElement('section');results.setAttribute('aria-live','polite');panel.append(results);
  const text=(node,value)=>{node.textContent=value;return node;};
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
        section.append(text(document.createElement('p'),d.processing_status+' | '+d.run_id));
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
        nodes.push(section);
      }
      results.replaceChildren(...nodes);
      if(p.active){state.textContent=fa?'استخراج در حال اجرا؛ نتایج هر سند جدا ذخیره می‌شود':'Extraktion läuft; Ergebnisse werden einzeln gespeichert';button.disabled=true;}
      else if(panel.dataset.executionStarted){state.textContent=fa?'وضعیت پایدار بازیابی شد؛ نتایج نیازمند بازبینی هستند':'Dauerhafter Status geladen; Ergebnisse benötigen Prüfung';}
    }catch(_){state.textContent=fa?'بازیابی وضعیت تأییدشده ممکن نیست':'Verifizierter Status nicht verfügbar';}
  }
  fetch('/cases/analysis/readiness?'+params,{credentials:'same-origin',cache:'no-store'}).then(r=>r.json()).then(d=>{
    if(d.inventory_verified===true&&d.analysis_launch_available===true&&d.case_id===panel.dataset.caseId&&String(d.tax_year)===panel.dataset.taxYear){
      button.disabled=false;button.setAttribute('aria-disabled','false');button.textContent=fa?'استخراج PDF با Gemini':'PDF mit Gemini extrahieren';
    }
  }).catch(()=>{});
  button.addEventListener('click',async()=>{
    if(button.disabled)return;button.disabled=true;button.setAttribute('aria-disabled','true');panel.dataset.executionStarted='true';
    try{
      const r=await fetch('/cases/analysis/execute',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:params});
      if(!r.ok)throw Error('HTTP_'+r.status);
      const receipt=await r.json();
      if(receipt.case_id!==panel.dataset.caseId||String(receipt.tax_year)!==panel.dataset.taxYear||!receipt.run_id)throw Error('INVALID_RECEIPT');
      state.textContent=(fa?'در صف Kernel؛ هنوز نتیجه نیست: ':'Im Kernel eingereiht; noch kein Ergebnis: ')+receipt.run_id;
      await progress();
    }catch(e){state.textContent=(fa?'شروع ناموفق: ':'Start fehlgeschlagen: ')+e.message;}
  });
  progress();setInterval(progress,2500);
})();
