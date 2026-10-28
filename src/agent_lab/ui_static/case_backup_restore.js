(() => {
  const year=document.getElementById('case-restore-year');
  const refresh=document.getElementById('case-restore-refresh');
  const list=document.getElementById('case-restore-list');
  const status=document.getElementById('case-restore-result');
  if (!year || !refresh || !list || !status) return;
  const fa=document.documentElement.lang==='fa-IR';
  const tr=(a,b)=>fa?a:b;
  let busy=false;
  async function load() {
    if(busy)return;
    busy=true;list.replaceChildren();
    status.textContent=tr('در حال بررسی پشتیبان‌ها...','Backups werden geprüft...');
    try {
      const res=await fetch('/cases/backup/available?tax_year='+encodeURIComponent(year.value),{credentials:'same-origin'});
      const data=await res.json();
      if(!res.ok)throw Error(data.reason||'HTTP '+res.status);
      status.textContent=data.backups.length?tr('نسخه‌های تأییدشده:','Verifizierte Backups:'):tr('پشتیبان قابل بازگردانی وجود ندارد.','Keine wiederherstellbaren Backups.');
      for(const entry of data.backups) {
        const line=document.createElement('p');
        const label=document.createElement('span');
        label.textContent=entry.case_id+' | '+entry.backup_id+' ';
        const button=document.createElement('button');
        button.type='button';
        button.textContent=tr('بازگرداندن این نسخه','Diese Version wiederherstellen');
        button.addEventListener('click',async()=>{
          if(busy)return;
          const message=tr('آیا بازگردانی پرونده '+entry.case_id+' از نسخه '+entry.backup_id+' را تأیید می‌کنید؟','Fall '+entry.case_id+' aus Backup '+entry.backup_id+' wiederherstellen?');
          if(!confirm(message))return;
          busy=true;button.disabled=true;
          status.textContent=tr('در حال بازگردانی و بررسی مدارک...','Wiederherstellung und Prüfung laufen...');
          try {
            const body=new FormData();
            for(const key of ['case_id','tax_year','backup_id'])body.set(key,entry[key]);
            body.set('confirmation',entry.case_id);
            const response=await fetch('/cases/backup/restore',{method:'POST',body,credentials:'same-origin'});
            const outcome=await response.json();
            if(!response.ok||!outcome.restored)throw Error(outcome.reason||'HTTP '+response.status);
            status.textContent=tr('پرونده و مدارک با موفقیت بازگردانده شدند.','Fall und Dokumente wiederhergestellt.');
            location.assign('/?tab=cases&case_id='+encodeURIComponent(entry.case_id)+'&lang='+encodeURIComponent(document.documentElement.lang));
          }catch(e){status.textContent=tr('بازگردانی ناموفق؛ وضعیت را بررسی کنید: ','Wiederherstellung fehlgeschlagen: ')+e.message;}
          finally{busy=false;button.disabled=false;}
        });
        const deleteButton=document.createElement('button');
        deleteButton.type='button';
        deleteButton.textContent=tr('حذف دائمی این پشتیبان','Dieses Backup endgültig löschen');
        deleteButton.addEventListener('click',async()=>{
          if(busy)return;
          const warning=tr(
            'هشدار: پشتیبان '+entry.backup_id+' برای '+entry.case_id+' برای همیشه از Google Drive حذف می‌شود و قابل بازگردانی نخواهد بود. ادامه می‌دهید؟',
            'WARNUNG: Backup '+entry.backup_id+' für '+entry.case_id+' wird unwiderruflich aus Google Drive gelöscht. Fortfahren?');
          if(!confirm(warning))return;
          const typed=prompt(tr('برای تأیید نهایی شناسه پرونده را دقیق وارد کنید: '+entry.case_id,
            'Zur endgültigen Bestätigung Fall-ID exakt eingeben: '+entry.case_id));
          if(typed!==entry.case_id)return;
          busy=true;deleteButton.disabled=true;button.disabled=true;
          status.textContent=tr('در حال حذف دائمی و بررسی آزادسازی شماره...','Endgültige Löschung und Freigabeprüfung...');
          try{
            const body=new FormData();
            for(const key of ['case_id','tax_year','backup_id'])body.set(key,entry[key]);
            body.set('confirmation','DELETE '+entry.case_id+' '+entry.backup_id);
            const response=await fetch('/cases/backup/delete',{method:'POST',body,credentials:'same-origin'});
            const outcome=await response.json();
            if(!response.ok||!outcome.deleted)throw Error(outcome.reason||'HTTP '+response.status);
            status.textContent=outcome.number_released
              ?tr('پشتیبان حذف شد و رزرو شماره آزاد شد.','Backup gelöscht; Fallnummer freigegeben.')
              :tr('پشتیبان حذف شد؛ شماره همچنان رزرو است.','Backup gelöscht; Fallnummer weiterhin reserviert.');
            line.remove();
          }catch(e){status.textContent=tr('حذف تأیید نشد. وضعیت را بررسی کنید: ','Löschung nicht bestätigt: ')+e.message;}
          finally{busy=false;deleteButton.disabled=false;button.disabled=false;}
        });
        line.append(label,button,deleteButton);list.append(line);
      }
    }catch(e){status.textContent=e.message;}
    finally{busy=false;}
  }
  refresh.addEventListener('click',load);
  load();
})();