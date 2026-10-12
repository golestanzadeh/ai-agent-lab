"""UI25-01 read-only dashboard: explicit authority, never synthetic live fallback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent_lab.ui_app import LOCAL_SECURITY_HEADERS, UI_ROOT


@dataclass(frozen=True, slots=True)
class DashboardCase:
    case_id: str
    tax_year: int
    status: str

    def __post_init__(self):
        if not self.case_id.strip() or self.case_id.startswith("SYNTH-"):
            raise ValueError("live dashboard requires a non-synthetic case identifier")
        if not 1900 <= self.tax_year <= 9999:
            raise ValueError("invalid tax year")
        if self.status not in {"CREATED", "ACTIVE", "PROCESSING", "REVIEW_REQUIRED", "COMPLETED", "ARCHIVED", "BLOCKED"}:
            raise ValueError("unverified lifecycle status")


class DashboardUnavailable(RuntimeError):
    """No independently verified, owner-authorized metadata source is connected."""


ReadCases = Callable[[], tuple[DashboardCase, ...]]

UI_TEXT = {
    "fa-IR": {"dir":"rtl","overview":"نمای کلی","cases":"پرونده‌ها","family":"خانواده","documents":"مدارک","analysis":"تحلیل","issues":"پرسش‌ها","result":"نتیجه","declaration":"اظهارنامه","approval":"تأیید و ارسال","activity":"فعالیت‌ها","heading":"نمای کلی پرونده‌های مالیاتی","privacy":"حریم خصوصی فعال","disabled":"غیرفعال","switch":"Deutsch","switch_code":"de-DE","submission":"ارسال به ELSTER غیرفعال است"},
    "de-DE": {"dir":"ltr","overview":"Übersicht","cases":"Steuerfälle","family":"Familie","documents":"Dokumente","analysis":"Analyse","issues":"Rückfragen","result":"Ergebnis","declaration":"Steuererklärung","approval":"Freigabe und Übermittlung","activity":"Aktivitäten","heading":"Übersicht der Steuerfälle","privacy":"Datenschutz aktiv","disabled":"Deaktiviert","switch":"فارسی","switch_code":"fa-IR","submission":"ELSTER-Übermittlung ist deaktiviert"},
}


# UI25 localization: all user-visible dashboard and tab copy is catalog-driven.
UI_TEXT['fa-IR']['page_title'] = 'داشبورد · AI Tax Agent'
UI_TEXT['de-DE']['page_title'] = 'Dashboard · AI Tax Agent'
UI_TEXT['fa-IR']['skip'] = 'رفتن به محتوا'
UI_TEXT['de-DE']['skip'] = 'Zum Inhalt springen'
UI_TEXT['fa-IR']['main_nav'] = 'ناوبری اصلی'
UI_TEXT['de-DE']['main_nav'] = 'Hauptnavigation'
UI_TEXT['fa-IR']['workspace'] = 'فضای کار'
UI_TEXT['de-DE']['workspace'] = 'Arbeitsbereich'
UI_TEXT['fa-IR']['tax_workspace'] = 'فضای کار مالیاتی'
UI_TEXT['de-DE']['tax_workspace'] = 'Steuerarbeitsbereich'
UI_TEXT['fa-IR']['local_readonly'] = 'محیط محلی · فقط خواندنی'
UI_TEXT['de-DE']['local_readonly'] = 'Lokale Umgebung · schreibgeschützt'
UI_TEXT['fa-IR']['next_status'] = 'وضعیت پرونده\u200cها و گام بعدی، در یک نگاه.'
UI_TEXT['de-DE']['next_status'] = 'Fallstatus und nächste Schritte im Überblick.'
UI_TEXT['fa-IR']['connected_source'] = '● اتصال به منبع تأییدشده'
UI_TEXT['de-DE']['connected_source'] = '● Verifizierte Datenquelle verbunden'
UI_TEXT['fa-IR']['disconnected_source'] = '● منبع پرونده متصل نیست'
UI_TEXT['de-DE']['disconnected_source'] = '● Falldatenquelle nicht verbunden'
UI_TEXT['fa-IR']['connection_missing'] = 'اتصال معتبر هنوز برقرار نشده است'
UI_TEXT['de-DE']['connection_missing'] = 'Noch keine verifizierte Verbindung'
UI_TEXT['fa-IR']['connection_explanation'] = 'تا زمانی که دسترسی فقط\u200cخواندنی به منبع معتبر پرونده\u200cها تأیید نشود، هیچ اطلاعات فرضی به\u200cعنوان پروندهٔ واقعی نمایش داده نمی\u200cشود.'
UI_TEXT['de-DE']['connection_explanation'] = 'Solange der schreibgeschützte Zugriff auf die verifizierte Falldatenquelle nicht bestätigt ist, werden keine erfundenen Falldaten angezeigt.'
UI_TEXT['fa-IR']['connection_dependency'] = 'وضعیت: اتصال نیازمند تکمیل قرارداد دسترسی Kernel و Persistence است.'
UI_TEXT['de-DE']['connection_dependency'] = 'Status: Die Anbindung erfordert einen freigegebenen Kernel-/Persistenz-Zugriffsvertrag.'
UI_TEXT['fa-IR']['no_cases'] = 'پرونده\u200cای برای نمایش وجود ندارد'
UI_TEXT['de-DE']['no_cases'] = 'Keine Fälle vorhanden'
UI_TEXT['fa-IR']['no_cases_description'] = 'منبع تأییدشده متصل است، اما پروندهٔ مجازی در محدودهٔ دسترسی فعلی وجود ندارد.'
UI_TEXT['de-DE']['no_cases_description'] = 'Die verifizierte Quelle ist verbunden, aber im aktuellen Zugriffsbereich sind keine Fälle vorhanden.'
UI_TEXT['fa-IR']['visible_cases'] = 'پرونده\u200cهای قابل مشاهده'
UI_TEXT['de-DE']['visible_cases'] = 'Sichtbare Fälle'
UI_TEXT['fa-IR']['authorized_source'] = 'از منبع مجاز'
UI_TEXT['de-DE']['authorized_source'] = 'Aus autorisierter Quelle'
UI_TEXT['fa-IR']['latest_tax_year'] = 'آخرین سال مالیاتی'
UI_TEXT['de-DE']['latest_tax_year'] = 'Letztes Steuerjahr'
UI_TEXT['fa-IR']['listed_year'] = 'ثبت\u200cشده در فهرست'
UI_TEXT['de-DE']['listed_year'] = 'In der Liste erfasst'
UI_TEXT['fa-IR']['selected_case_status'] = 'وضعیت پروندهٔ انتخابی'
UI_TEXT['de-DE']['selected_case_status'] = 'Status des ausgewählten Falls'
UI_TEXT['fa-IR']['verified_data'] = 'بر اساس دادهٔ معتبر'
UI_TEXT['de-DE']['verified_data'] = 'Auf Basis verifizierter Daten'
UI_TEXT['fa-IR']['your_cases'] = 'پرونده\u200cهای شما'
UI_TEXT['de-DE']['your_cases'] = 'Ihre Steuerfälle'
UI_TEXT['fa-IR']['case_list'] = 'فهرست پرونده\u200cها'
UI_TEXT['de-DE']['case_list'] = 'Fallübersicht'
UI_TEXT['fa-IR']['read_only'] = 'فقط خواندنی'
UI_TEXT['de-DE']['read_only'] = 'Schreibgeschützt'
UI_TEXT['fa-IR']['tax_year'] = 'سال مالیاتی'
UI_TEXT['de-DE']['tax_year'] = 'Steuerjahr'
UI_TEXT['fa-IR']['next_step'] = 'مرحلهٔ بعد'
UI_TEXT['de-DE']['next_step'] = 'Nächster Schritt'
UI_TEXT['fa-IR']['secure_connection'] = 'اتصال امن به پرونده\u200cهای واقعی'
UI_TEXT['de-DE']['secure_connection'] = 'Sichere Anbindung realer Steuerfälle'
UI_TEXT['fa-IR']['secure_connection_detail'] = 'پس از تأیید منبع داده، جزئیات پرونده، مدارک و وظایف بدون نمایش اطلاعات ساختگی فعال می\u200cشوند.'
UI_TEXT['de-DE']['secure_connection_detail'] = 'Nach Freigabe der Datenquelle werden Falldetails, Dokumente und Aufgaben ohne erfundene Angaben verfügbar.'
UI_TEXT['fa-IR']['test_banner'] = 'TEST ONLY · محیط آزمایش عملکردی'
UI_TEXT['de-DE']['test_banner'] = 'NUR TEST · Funktionale Testumgebung'
UI_TEXT['fa-IR']['test_banner_description'] = 'پرونده\u200cهای TEST واقعیِ مالیاتی نیستند. عملیات این محیط فقط در پایگاه دادهٔ آزمایشی محلی ثبت می\u200cشوند.'
UI_TEXT['de-DE']['test_banner_description'] = 'TEST-Fälle sind keine echten Steuerfälle. Aktionen werden ausschließlich in der lokalen Testdatenbank gespeichert.'
UI_TEXT['fa-IR']['cases_heading'] = 'پرونده\u200cها و سال مالیاتی'
UI_TEXT['de-DE']['cases_heading'] = 'Steuerfälle und Steuerjahre'
UI_TEXT['fa-IR']['cases_desc'] = 'ایجاد، انتخاب و بازکردن پرونده\u200cهای مالیاتی'
UI_TEXT['de-DE']['cases_desc'] = 'Steuerfälle anlegen, auswählen und wieder öffnen'
UI_TEXT['fa-IR']['family_heading'] = 'خانواده و اشخاص'
UI_TEXT['de-DE']['family_heading'] = 'Familie und Personen'
UI_TEXT['fa-IR']['family_desc'] = 'هویت، اعضای خانواده و انتقال کنترل\u200cشدهٔ اطلاعات سال قبل'
UI_TEXT['de-DE']['family_desc'] = 'Identitäten, Familienmitglieder und kontrollierte Übernahme aus dem Vorjahr'
UI_TEXT['fa-IR']['documents_heading'] = 'مدارک پرونده'
UI_TEXT['de-DE']['documents_heading'] = 'Falldokumente'
UI_TEXT['fa-IR']['documents_desc'] = 'دریافت تدریجی مدارک، شناسایی تکراری\u200cها و مدیریت نسخه\u200cها'
UI_TEXT['de-DE']['documents_desc'] = 'Schrittweiser Dokumenteneingang, Dublettenprüfung und Versionierung'
UI_TEXT['fa-IR']['analysis_heading'] = 'تحلیل و شواهد'
UI_TEXT['de-DE']['analysis_heading'] = 'Analyse und Nachweise'
UI_TEXT['fa-IR']['analysis_desc'] = 'نتایج استخراج، تحلیل ایجنت\u200cها و ارتباط هر یافته با شواهد'
UI_TEXT['de-DE']['analysis_desc'] = 'Extraktionsergebnisse, Agentenanalysen und Nachweisbezüge'
UI_TEXT['fa-IR']['issues_heading'] = 'پرسش\u200cها و موارد باز'
UI_TEXT['de-DE']['issues_heading'] = 'Rückfragen und offene Punkte'
UI_TEXT['fa-IR']['issues_desc'] = 'سؤال\u200cهای قابل پیگیری و موارد نیازمند تصمیم انسانی'
UI_TEXT['de-DE']['issues_desc'] = 'Nachverfolgbare Rückfragen und erforderliche Entscheidungen'
UI_TEXT['fa-IR']['result_heading'] = 'نتیجهٔ محاسبه'
UI_TEXT['de-DE']['result_heading'] = 'Berechnungsergebnis'
UI_TEXT['fa-IR']['result_desc'] = 'نتایج نسخه\u200cبندی\u200cشده و مقایسهٔ تغییرات'
UI_TEXT['de-DE']['result_desc'] = 'Versionierte Ergebnisse und Änderungsvergleich'
UI_TEXT['fa-IR']['declaration_heading'] = 'پیش\u200cنمایش اظهارنامه'
UI_TEXT['de-DE']['declaration_heading'] = 'Vorschau der Steuererklärung'
UI_TEXT['fa-IR']['declaration_desc'] = 'مشاهدهٔ فرم پیش از تأیید، بدون ارسال'
UI_TEXT['de-DE']['declaration_desc'] = 'Formularvorschau vor der Freigabe, ohne Übermittlung'
UI_TEXT['fa-IR']['approval_heading'] = 'تأیید و ارسال'
UI_TEXT['de-DE']['approval_heading'] = 'Freigabe und Übermittlung'
UI_TEXT['fa-IR']['approval_desc'] = 'دو مجوز مستقل برای صحت محتوا و مقصد ارسال'
UI_TEXT['de-DE']['approval_desc'] = 'Zwei getrennte Freigaben für Inhalt und Übermittlungsziel'
UI_TEXT['fa-IR']['activity_heading'] = 'تاریخچه و فعالیت\u200cها'
UI_TEXT['de-DE']['activity_heading'] = 'Verlauf und Aktivitäten'
UI_TEXT['fa-IR']['activity_desc'] = 'رویدادها، شواهد اجرا و ردپای ممیزی'
UI_TEXT['de-DE']['activity_desc'] = 'Ereignisse, Ausführungsnachweise und Prüfprotokoll'
UI_TEXT['fa-IR']['connection_status'] = 'وضعیت اتصال'
UI_TEXT['de-DE']['connection_status'] = 'Verbindungsstatus'
UI_TEXT['fa-IR']['local_safe_readonly'] = 'محیط امن · فقط خواندنی'
UI_TEXT['de-DE']['local_safe_readonly'] = 'Geschützte Umgebung · schreibgeschützt'
UI_TEXT['fa-IR']['not_verified'] = '● اتصال تأییدنشده'
UI_TEXT['de-DE']['not_verified'] = '● Verbindung nicht verifiziert'
UI_TEXT['fa-IR']['verified'] = '● منبع معتبر متصل'
UI_TEXT['de-DE']['verified'] = '● Verifizierte Quelle verbunden'
UI_TEXT['fa-IR']['no_live_data'] = 'دادهٔ واقعی هنوز قابل نمایش نیست'
UI_TEXT['de-DE']['no_live_data'] = 'Echte Falldaten noch nicht verfügbar'
UI_TEXT['fa-IR']['no_live_data_desc'] = 'اتصال مجاز به رجیستری پایدار پرونده\u200cها در این نشست تأیید نشده است. برای جلوگیری از نمایش اطلاعات گمراه\u200cکننده، داده\u200cای ساخته یا حدس زده نمی\u200cشود.'
UI_TEXT['de-DE']['no_live_data_desc'] = 'Der autorisierte Zugriff auf das dauerhafte Fallregister ist in dieser Sitzung nicht bestätigt. Es werden keine Daten erfunden oder geschätzt.'
UI_TEXT['fa-IR']['case_label'] = 'پرونده:'
UI_TEXT['de-DE']['case_label'] = 'Fall:'
UI_TEXT['fa-IR']['year_label'] = 'سال:'
UI_TEXT['de-DE']['year_label'] = 'Jahr:'
UI_TEXT['fa-IR']['status_label'] = 'وضعیت:'
UI_TEXT['de-DE']['status_label'] = 'Status:'
UI_TEXT['fa-IR']['selected_verified'] = 'هویت پرونده از منبع مجاز خوانده شده است؛ داده\u200cهای تخصصی این بخش تنها پس از تأیید قرارداد دسترسی همان سرویس نمایش داده می\u200cشوند.'
UI_TEXT['de-DE']['selected_verified'] = 'Die Fallidentität stammt aus einer autorisierten Quelle. Fachliche Daten werden erst nach Freigabe des jeweiligen Dienstzugriffs angezeigt.'
UI_TEXT['fa-IR']['no_scope_cases'] = 'در محدودهٔ مجاز پرونده\u200cای وجود ندارد.'
UI_TEXT['de-DE']['no_scope_cases'] = 'Keine Fälle im autorisierten Zugriffsbereich.'
UI_TEXT['fa-IR']['service_label'] = 'سرویس مربوطه'
UI_TEXT['de-DE']['service_label'] = 'Zugehöriger Dienst'
UI_TEXT['fa-IR']['service_not_verified'] = 'وضعیت: اتصال عملیاتی این تب هنوز تأیید نشده است.'
UI_TEXT['de-DE']['service_not_verified'] = 'Status: Die operative Anbindung dieses Bereichs ist noch nicht bestätigt.'
UI_TEXT['fa-IR']['gate1'] = '۱. تأیید صحت محتوا'
UI_TEXT['de-DE']['gate1'] = '1. Inhaltliche Freigabe'
UI_TEXT['fa-IR']['gate2'] = '۲. مجوز مقصد و ارسال'
UI_TEXT['de-DE']['gate2'] = '2. Freigabe von Ziel und Übermittlung'
UI_TEXT['fa-IR']['not_recorded'] = 'ثبت نشده'
UI_TEXT['de-DE']['not_recorded'] = 'Nicht erteilt'
UI_TEXT['fa-IR']['elster_disabled'] = 'ارسال به ELSTER غیرفعال است'
UI_TEXT['de-DE']['elster_disabled'] = 'ELSTER-Übermittlung ist deaktiviert'
UI_TEXT['fa-IR']['test_controls'] = 'محیط تست عملکردی (TEST ONLY)'
UI_TEXT['de-DE']['test_controls'] = 'Funktionale Testumgebung (NUR TEST)'
UI_TEXT['fa-IR']['test_warning'] = 'داده\u200cهای این بخش آزمایشی و محلی هستند. این محیط به پرونده\u200cهای واقعی، Kernel اجرایی یا ELSTER متصل نیست. فایل واقعی مالیاتی بارگذاری نکنید.'
UI_TEXT['de-DE']['test_warning'] = 'Diese Daten sind lokal und ausschließlich zu Testzwecken. Keine Verbindung zu echten Steuerfällen, dem produktiven Kernel oder ELSTER. Keine echten Steuerunterlagen hochladen.'
UI_TEXT['fa-IR']['create_test_case'] = 'ساخت پروندهٔ آزمایشی'
UI_TEXT['de-DE']['create_test_case'] = 'Testfall anlegen'
UI_TEXT['fa-IR']['test_id_label'] = 'شناسه (با TEST- شروع شود)'
UI_TEXT['de-DE']['test_id_label'] = 'Kennung (beginnt mit TEST-)'
UI_TEXT['fa-IR']['create_test_button'] = 'ایجاد پروندهٔ آزمایشی'
UI_TEXT['de-DE']['create_test_button'] = 'Testfall erstellen'
UI_TEXT['fa-IR']['select_test_case'] = 'انتخاب پروندهٔ آزمایشی'
UI_TEXT['de-DE']['select_test_case'] = 'Testfall auswählen'
UI_TEXT['fa-IR']['test_document_heading'] = 'ثبت هش مدرک آزمایشی'
UI_TEXT['de-DE']['test_document_heading'] = 'Prüfsumme eines Testdokuments erfassen'
UI_TEXT['fa-IR']['test_document_desc'] = 'فایل فقط برای محاسبهٔ SHA-256 خوانده می\u200cشود؛ محتوای آن ذخیره نمی\u200cشود.'
UI_TEXT['de-DE']['test_document_desc'] = 'Die Datei wird nur zur Berechnung von SHA-256 gelesen; ihr Inhalt wird nicht gespeichert.'
UI_TEXT['fa-IR']['document_title'] = 'عنوان مدرک'
UI_TEXT['de-DE']['document_title'] = 'Dokumenttitel'
UI_TEXT['fa-IR']['test_file_label'] = 'فایل آزمایشی (حداکثر ۲ مگابایت)'
UI_TEXT['de-DE']['test_file_label'] = 'Testdatei (maximal 2 MB)'
UI_TEXT['fa-IR']['duplicate_button'] = 'ثبت و بررسی تکراری'
UI_TEXT['de-DE']['duplicate_button'] = 'Erfassen und auf Duplikate prüfen'
UI_TEXT['fa-IR']['saved_documents'] = 'مدارک ثبت\u200cشده'
UI_TEXT['de-DE']['saved_documents'] = 'Erfasste Dokumente'
UI_TEXT['fa-IR']['no_documents'] = 'هنوز مدرکی ثبت نشده است.'
UI_TEXT['de-DE']['no_documents'] = 'Noch keine Dokumente erfasst.'
UI_TEXT['fa-IR']['test_question'] = 'ثبت پرسش آزمایشی'
UI_TEXT['de-DE']['test_question'] = 'Test-Rückfrage erfassen'
UI_TEXT['fa-IR']['question'] = 'پرسش'
UI_TEXT['de-DE']['question'] = 'Rückfrage'
UI_TEXT['fa-IR']['save_question'] = 'ثبت پرسش'
UI_TEXT['de-DE']['save_question'] = 'Rückfrage speichern'
UI_TEXT['fa-IR']['case_questions'] = 'پرسش\u200cهای پرونده'
UI_TEXT['de-DE']['case_questions'] = 'Rückfragen zum Fall'
UI_TEXT['fa-IR']['answer'] = 'پاسخ'
UI_TEXT['de-DE']['answer'] = 'Antwort'
UI_TEXT['fa-IR']['save_answer'] = 'ثبت پاسخ'
UI_TEXT['de-DE']['save_answer'] = 'Antwort speichern'
UI_TEXT['fa-IR']['no_questions'] = 'پرسشی ثبت نشده است.'
UI_TEXT['de-DE']['no_questions'] = 'Noch keine Rückfragen erfasst.'
UI_TEXT['fa-IR']['test_history'] = 'تاریخچهٔ آزمایشی پرونده'
UI_TEXT['de-DE']['test_history'] = 'Test-Fallverlauf'
UI_TEXT['fa-IR']['no_events'] = 'رویدادی ثبت نشده است.'
UI_TEXT['de-DE']['no_events'] = 'Noch keine Ereignisse erfasst.'
UI_TEXT['fa-IR']['stats_aria'] = 'خلاصهٔ پرونده‌ها'
UI_TEXT['de-DE']['stats_aria'] = 'Fallübersicht'
UI_TEXT['fa-IR']['status_labels'] = {
    'CREATED':'ایجادشده','ACTIVE':'فعال','PROCESSING':'در حال پردازش',
    'REVIEW_REQUIRED':'نیازمند بررسی','COMPLETED':'تکمیل‌شده',
    'ARCHIVED':'بایگانی‌شده','BLOCKED':'مسدود'
}
UI_TEXT['de-DE']['status_labels'] = {
    'CREATED':'Angelegt','ACTIVE':'Aktiv','PROCESSING':'In Bearbeitung',
    'REVIEW_REQUIRED':'Prüfung erforderlich','COMPLETED':'Abgeschlossen',
    'ARCHIVED':'Archiviert','BLOCKED':'Gesperrt'
}



def create_dashboard_app(*, read_cases: ReadCases | None = None, test_store=None) -> FastAPI:
    """Expose a fail-closed dashboard; caller must inject an authorized live resolver.

    This is not a substitute for the Kernel's permission or persistence layer.
    No fake cases, inferred 2024 status or case data are returned by default.
    """
    if test_store is not None and read_cases is not None:
        raise ValueError("test store and live case resolver must never be mixed")
    if test_store is not None:
        read_cases = test_store.cases
    app = FastAPI(title="AI-Tax-Agent Dashboard", docs_url=None, redoc_url=None, openapi_url=None)
    templates = Jinja2Templates(directory=str(UI_ROOT / "ui_templates"))
    app.mount("/static", StaticFiles(directory=str(UI_ROOT / "ui_static")), name="static")

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        if test_store is not None and request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin not in (None, "http://127.0.0.1:8766"):
                from fastapi.responses import PlainTextResponse
                return PlainTextResponse("Cross-origin mutation rejected", status_code=403)
        response = await call_next(request)
        for name, value in LOCAL_SECURITY_HEADERS.items():
            response.headers[name] = value
        if test_store is not None:
            response.headers["content-security-policy"] = response.headers["content-security-policy"].replace("form-action "+chr(39)+"none"+chr(39), "form-action "+chr(39)+"self"+chr(39))
        return response

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, case_id: str | None = None, tab: str = "overview", lang: str = "fa-IR"):
        tabs = {"overview", "cases", "family", "documents", "analysis", "issues", "result", "declaration", "approval", "activity"}
        if tab not in tabs:
            raise HTTPException(status_code=404, detail="Unknown workspace tab")
        if lang not in UI_TEXT:
            raise HTTPException(status_code=404, detail="Unsupported language")
        state = "unavailable"
        cases: tuple[DashboardCase, ...] = ()
        selected = None
        if read_cases is not None:
            try:
                loaded = read_cases()
                if not isinstance(loaded, tuple) or any(not isinstance(item, DashboardCase) for item in loaded):
                    raise DashboardUnavailable("invalid source response")
                ids = [item.case_id for item in loaded]
                if len(set(ids)) != len(ids):
                    raise DashboardUnavailable("ambiguous case identities")
                cases = tuple(sorted(loaded, key=lambda item: (-item.tax_year, item.case_id)))
                state = "connected"
                if case_id is not None and case_id not in ids:
                    raise HTTPException(status_code=404, detail="Case not found")
                selected = next((item for item in cases if item.case_id == case_id), None) if case_id else (cases[0] if cases else None)
            except DashboardUnavailable:
                if case_id is not None:
                    raise HTTPException(status_code=503, detail="Verified case source unavailable")
                state = "unavailable"
                cases = ()
                selected = None
        elif case_id is not None:
            raise HTTPException(status_code=503, detail="Verified case source unavailable")
        detail = None
        if test_store is not None and selected is not None:
            detail = test_store.detail(selected.case_id)
        return templates.TemplateResponse(request=request, name="dashboard.html", context={
            "state": state, "cases": cases, "selected": selected, "tab": tab,
            "test_mode": test_store is not None, "detail": detail, "lang": lang, "t": UI_TEXT[lang],
        })

    def require_test():
        if test_store is None:
            raise HTTPException(status_code=404, detail="Test operations unavailable")

    @app.post("/test/cases")
    async def create_test_case(case_id: str = Form(...), tax_year: int = Form(...)):
        require_test()
        try:
            test_store.create_case(case_id, tax_year)
        except (ValueError, __import__("sqlite3").IntegrityError):
            raise HTTPException(status_code=400, detail="Invalid or duplicate test case")
        return RedirectResponse("/?tab=cases&case_id="+case_id, status_code=303)

    @app.post("/test/documents")
    async def add_test_document(case_id: str = Form(...), label: str = Form(...), document: UploadFile = File(...)):
        require_test()
        data = await document.read(2_000_001)
        try:
            added = test_store.add_document(case_id, label, data)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid test document or case")
        return RedirectResponse("/?tab=documents&case_id="+case_id+"&added="+str(int(added)), status_code=303)

    @app.post("/test/issues")
    async def create_test_issue(case_id: str = Form(...), question: str = Form(...)):
        require_test()
        try:
            test_store.add_issue(case_id, question)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid test question or case")
        return RedirectResponse("/?tab=issues&case_id="+case_id, status_code=303)

    @app.post("/test/issues/answer")
    async def answer_test_issue(case_id: str = Form(...), issue_id: int = Form(...), answer: str = Form(...)):
        require_test()
        try:
            test_store.answer_issue(case_id, issue_id, answer)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid test issue or answer")
        return RedirectResponse("/?tab=issues&case_id="+case_id, status_code=303)

    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": "isolated-functional-test" if test_store is not None else "read-only-dashboard", "source": "test-only" if test_store is not None else ("configured" if read_cases else "unavailable")}

    return app
