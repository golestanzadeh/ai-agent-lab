"""Read-only Owner preview of Gemini document extraction; never accepts model output as tax truth."""
from __future__ import annotations
import json
import os
from html import escape
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/cases/analysis/gemini-preview", response_class=HTMLResponse)
def gemini_preview(case_id: str, tax_year: int):
    if case_id != "CASE-2025-0001" or tax_year != 2025:
        raise HTTPException(404, "No preview for this case")
    path = Path(os.environ["LOCALAPPDATA"]) / "AI-Tax-Agent" / "Cases" / "gemini-case001-preview.json"
    if not path.is_file():
        raise HTTPException(404, "No completed extraction preview")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("case_id") != case_id or data.get("tax_year") != tax_year or data.get("status") != "EXTRACTION_PREVIEW_ONLY_NOT_ACCEPTED":
        raise HTTPException(409, "Preview identity mismatch")
    def e(v): return escape(str(v), quote=True)
    rows = "".join("<tr><td>"+e(f.get("name",""))+"</td><td>"+e(f.get("value",""))+"</td><td>"+e(f.get("page",""))+"</td><td>"+e(f.get("evidence",""))+"</td></tr>" for f in data.get("fields",[]))
    html = ('<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><title>Gemini | CASE-2025-0001</title>'
            '<style>body{font:16px system-ui;max-width:1100px;margin:30px auto;padding:15px}table{width:100%;border-collapse:collapse;direction:ltr;text-align:left}td,th{border:1px solid #bbb;padding:9px;overflow-wrap:anywhere}header{background:#eef;padding:16px}a{color:#175bba}</style>'
            '<header><a href="/?tab=analysis&case_id=CASE-2025-0001&lang=fa-IR">بازگشت به داشبورد</a>'
            '<h1>نتیجه واقعی استخراج Gemini</h1><p>فقط پیش‌نمایش؛ هنوز تأیید مالیاتی یا مجوز انتقال سند نیست.</p></header>'
            '<p>پرونده: '+e(case_id)+' | سال: '+e(tax_year)+'</p>'
            '<p>سند: '+e(data["filename"])+' | نوع: '+e(data["document_type"])+'</p>'
            '<p>دسته‌بندی پیشنهادی: '+e(data["tax_category_candidate"])+' | اطمینان: '+e(data["confidence"])+'</p>'
            '<p>نیاز به بررسی انسانی: '+('بله' if data["needs_human_review"] else 'خیر')+'</p>'
            '<table><thead><tr><th>Field</th><th>Value</th><th>Page</th><th>Evidence</th></tr></thead><tbody>'+rows+'</tbody></table></html>')
    return HTMLResponse(html,headers={"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"})
