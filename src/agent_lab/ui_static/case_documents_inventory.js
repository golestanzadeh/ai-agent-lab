(() => {
'use strict';
const panel=document.getElementById('case-documents-list');
const button=document.getElementById('case-documents-refresh');
if(!panel||!button)return;
const fa=panel.dataset.lang==='fa-IR';
const load=async()=>{
button.disabled=true;
panel.textContent=fa?'در حال دریافت مدارک...':'Dokumente werden geladen...';
try{
const query=new URLSearchParams({case_id:panel.dataset.caseId,tax_year:panel.dataset.taxYear});
const response=await fetch('/cases/documents/inventory?'+query.toString(),{credentials:'same-origin',headers:{Accept:'application/json'}});
const data=await response.json();
if(!response.ok||!data.ready||data.case_id!==panel.dataset.caseId)throw Error('scope');
panel.replaceChildren();
if(!data.files.length){
panel.textContent=fa?'???? ????? ???? ??? ?????? ???? ?????.':'Noch keine Dokumente f?r diesen Fall.';
}else{
const list=document.createElement('ul');
for(const file of data.files){const item=document.createElement('li');item.textContent=file.name;list.appendChild(item);}
panel.appendChild(list);
}
}catch(_){panel.textContent=fa?'????? ????? ?? ????? ????. ??? ?????? ????? ???.':'Dokumentenliste nicht verf?gbar. Keine ?nderungen.';}
finally{button.disabled=false;}
};
button.addEventListener('click',load);load();
})();
