"""UI25-01 read-only dashboard: explicit authority, never synthetic live fallback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlencode

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
ReadKernelProjection = Callable[[str, int, str], object]
ExecuteKernelTask = Callable[..., object]

UI_TEXT = {
    "fa-IR": {
        "dir": "rtl", "title": "داشبورد", "skip": "رفتن به محتوا",
        "brand_subtitle": "فضای کار مالیاتی", "workspace": "فضای کار", "nav_label": "ناوبری اصلی",
        "local_readonly": "محیط محلی · فقط خواندنی",
        "overview": "نمای کلی", "cases": "پرونده‌ها", "family": "خانواده",
        "documents": "مدارک", "analysis": "تحلیل", "issues": "پرسش‌ها",
        "result": "نتیجه", "declaration": "اظهارنامه",
        "approval": "تأیید و ارسال", "activity": "فعالیت‌ها",
        "heading": "نمای کلی پرونده‌های مالیاتی", "privacy": "حریم خصوصی فعال",
        "disabled": "غیرفعال", "switch": "Deutsch", "switch_code": "de-DE",
        "submission": "ارسال به ELSTER غیرفعال است",
        "overview_subtitle": "وضعیت پرونده‌ها و گام بعدی، در یک نگاه.",
        "source_connected": "● اتصال به منبع تأییدشده",
        "source_unavailable": "● منبع پرونده متصل نیست",
        "connection_missing_title": "اتصال معتبر هنوز برقرار نشده است",
        "connection_missing_body": "تا زمانی که دسترسی فقط‌خواندنی به منبع معتبر پرونده‌ها تأیید نشود، هیچ اطلاعات فرضی به‌عنوان پروندهٔ واقعی نمایش داده نمی‌شود.",
        "connection_missing_detail": "وضعیت: اتصال نیازمند تکمیل قرارداد دسترسی Kernel و Persistence است.",
        "empty_title": "پرونده‌ای برای نمایش وجود ندارد",
        "empty_body": "منبع تأییدشده متصل است، اما پرونده‌ای در محدودهٔ دسترسی فعلی وجود ندارد.",
        "summary": "خلاصهٔ پرونده‌ها", "visible_cases": "پرونده‌های قابل مشاهده",
        "authorized_source": "از منبع مجاز", "latest_year": "آخرین سال مالیاتی",
        "registered_list": "ثبت‌شده در فهرست", "selected_status": "وضعیت پروندهٔ انتخابی",
        "verified_data": "بر اساس دادهٔ معتبر", "your_cases": "پرونده‌های شما",
        "case_list": "فهرست پرونده‌ها", "readonly": "فقط خواندنی", "tax_year": "سال مالیاتی",
        "next": "مرحلهٔ بعد", "next_title": "اتصال امن به پرونده‌های واقعی",
        "next_body": "پس از تأیید منبع داده، جزئیات پرونده، مدارک و وظایف بدون نمایش اطلاعات ساختگی فعال می‌شوند.",
        "connection_status": "وضعیت اتصال", "secure_readonly": "محیط امن · فقط خواندنی",
        "real_unavailable": "دادهٔ واقعی هنوز قابل نمایش نیست",
        "real_unavailable_body": "اتصال مجاز به رجیستری پایدار پرونده‌ها در این نشست تأیید نشده است. برای جلوگیری از نمایش اطلاعات گمراه‌کننده، داده‌ای ساخته یا حدس زده نمی‌شود.",
        "no_case": "در محدودهٔ مجاز پرونده‌ای وجود ندارد.", "case": "پرونده",
        "year": "سال", "status": "وضعیت", "verified_case_body": "هویت پرونده از منبع مجاز خوانده شده است؛ داده‌های تخصصی این بخش تنها پس از تأیید قرارداد دسترسی همان سرویس نمایش داده می‌شوند.",
        "related_service": "سرویس مربوطه", "service_unverified": "وضعیت: اتصال عملیاتی این تب هنوز تأیید نشده است.",
        "content_approval": "۱. تأیید صحت محتوا", "destination_approval": "۲. مجوز مقصد و ارسال",
        "not_recorded": "ثبت نشده", "workspace_eyebrow": "فضای کار",
        "test_only_title": "فقط آزمایش · محیط تست عملکردی",
        "test_only_body": "پرونده‌های TEST واقعیِ مالیاتی نیستند. وضعیت آن‌ها از backend آزمایشی محلی خوانده می‌شود.",
        "test_controls": "کنترل‌های تست عملکردی", "test_create_case": "ساخت پروندهٔ آزمایشی",
        "test_case_id": "شناسه (با TEST- شروع شود)", "test_tax_year": "سال مالیاتی",
        "test_create": "ایجاد پروندهٔ آزمایشی", "test_choose_case": "انتخاب پروندهٔ آزمایشی",
        "test_doc_register": "۱. ثبت سند مصنوعی", "test_doc_help": "فقط فایل متنی UTF-8 مصنوعی تا ۳۲ کیلوبایت مجاز است. byteهای آن فقط در پایگاه محلی تست برای بازخوانی ذخیره می‌شوند و هیچ ارسال خارجی انجام نمی‌شود.",
        "test_doc_label": "عنوان مدرک", "test_doc_file": "فایل UTF-8 آزمایشی (حداکثر ۳۲ کیلوبایت)",
        "test_doc_submit": "ثبت و بررسی تکراری", "test_doc_list": "مدارک ثبت‌شده",
        "test_doc_empty": "هنوز مدرکی ثبت نشده است.",
        "test_doc_process": "۲. فقط تطبیق digest در Kernel", "test_doc_run": "شناسه اجرای یکتا",
        "test_doc_extract": "۳. استخراج فیلدهای fixture مصنوعی", "synthetic_extraction_label": "استخراج محتوای مصنوعی — تحلیل مالیاتی نیست",
        "test_doc_validate_help": "فقط مالکیت سند و تطابق digest را بررسی می‌کند؛ محتوایی استخراج نمی‌شود.",
        "test_doc_extract_help": "byteهای سند را با قالب بستهٔ fixture خوانده، فیلدها را استخراج می‌کند و شما را مستقیم به نتیجهٔ Analysis می‌برد.",
        "test_doc_format": "قالب پشتیبانی‌شده: text/plain با UTF-8 و شش خط دقیق DOCUMENT_TYPE، TAX_YEAR، EMPLOYER_ID، GROSS_EMPLOYMENT_INCOME، WITHHELD_WAGE_TAX و CURRENCY=EUR. PDF، تصویر، فایل بانکی و سند واقعی پشتیبانی نمی‌شود.",
        "test_doc_unavailable": "اجرای Kernel در این launcher فعال نیست؛ رابط را با launcher رسمی تست باز کنید.",
        "analysis_result_title": "فیلدهای استخراج‌شدهٔ تأییدشده", "analysis_find": "پس از استخراج موفق، نتیجه در همین بخش Analysis نمایش داده می‌شود.",
        "ui_errors": {"unsupported_upload": "ثبت انجام نشد: فقط فایل text/plain مصنوعی تا ۳۲ کیلوبایت مجاز است.", "unsupported_fixture": "استخراج انجام نشد: سند انتخاب‌شده fixture مصنوعی پشتیبانی‌شده نیست یا محتوا/digest آن معتبر نیست."},
        "extraction_fields": {"DOCUMENT_REFERENCE": "مرجع سند", "DOCUMENT_DIGEST": "digest سند", "PARSER_SCHEMA": "نسخهٔ parser", "EXTRACTION_DIGEST": "digest استخراج", "DOCUMENT_TYPE": "نوع سند", "TAX_YEAR": "سال مالیاتی", "EMPLOYER_ID": "شناسهٔ کارفرمای مصنوعی", "GROSS_EMPLOYMENT_INCOME": "درآمد ناخالص استخدام", "WITHHELD_WAGE_TAX": "مالیات حقوق کسرشده", "CURRENCY": "ارز"},
        "kernel_title": "وضعیت واقعی Kernel", "kernel_run": "اجرای Kernel",
        "kernel_kill_switch": "کلید توقف", "kernel_tasks": "وظایف ثبت‌شده",
        "kernel_readonly": "این وضعیت مستقیماً و فقط‌خواندنی از Kernel خوانده شده است؛ اجرا فقط با اقدام صریح کاربر آغاز می‌شود.",
        "kernel_execute_title": "اجرای آزمایشی Kernel", "kernel_run_id": "شناسه اجرای آزمایشی",
        "kernel_value": "مقدار صحیح آزمایشی", "kernel_execute": "اجرای یک وظیفه آزمایشی",
        "kernel_result": "نتیجه قطعی worker", "kernel_pending": "نیازمند پذیرش مستقل",
        "status_labels": {
            "CREATED": "ایجادشده", "ACTIVE": "فعال", "PROCESSING": "در حال پردازش",
            "REVIEW_REQUIRED": "نیازمند بررسی", "COMPLETED": "تکمیل‌شده",
            "ARCHIVED": "بایگانی‌شده", "BLOCKED": "مسدود",
        },
        "pages": {
            "cases": ("پرونده‌ها و سال مالیاتی", "ایجاد، انتخاب و بازکردن پرونده‌های مالیاتی", "Case Registry / CaseCreationWorkflow"),
            "family": ("خانواده و اشخاص", "هویت، اعضای خانواده و انتقال کنترل‌شدهٔ اطلاعات سال قبل", "IdentityPersistence / CaseIdentityAssociationService"),
            "documents": ("مدارک پرونده", "دریافت تدریجی مدارک، شناسایی تکراری‌ها و مدیریت نسخه‌ها", "Case-scoped storage / document identity"),
            "analysis": ("تحلیل و شواهد", "نتایج استخراج، تحلیل ایجنت‌ها و ارتباط هر یافته با شواهد", "Deterministic Kernel / Gemini extraction boundary"),
            "issues": ("پرسش‌ها و موارد باز", "سؤال‌های قابل پیگیری و موارد نیازمند تصمیم انسانی", "Issues / Human Gates"),
            "result": ("نتیجهٔ محاسبه", "نتایج نسخه‌بندی‌شده و مقایسهٔ تغییرات", "Deterministic tax calculation"),
            "declaration": ("پیش‌نمایش اظهارنامه", "مشاهدهٔ فرم پیش از تأیید، بدون ارسال", "Declaration / ERiC validation"),
            "approval": ("تأیید و ارسال", "دو مجوز مستقل برای صحت محتوا و مقصد ارسال", "Human Gate 1 / Human Gate 2"),
            "activity": ("تاریخچه و فعالیت‌ها", "رویدادها، شواهد اجرا و ردپای ممیزی", "Audit / Checkpoint"),
        },
    },
    "de-DE": {
        "dir": "ltr", "title": "Dashboard", "skip": "Zum Inhalt springen",
        "brand_subtitle": "Steuerarbeitsbereich", "workspace": "Arbeitsbereich", "nav_label": "Hauptnavigation",
        "local_readonly": "Lokale Umgebung · schreibgeschützt",
        "overview": "Übersicht", "cases": "Steuerfälle", "family": "Familie",
        "documents": "Dokumente", "analysis": "Analyse", "issues": "Rückfragen",
        "result": "Ergebnis", "declaration": "Steuererklärung",
        "approval": "Freigabe und Übermittlung", "activity": "Aktivitäten",
        "heading": "Übersicht der Steuerfälle", "privacy": "Datenschutz aktiv",
        "disabled": "Deaktiviert", "switch": "فارسی", "switch_code": "fa-IR",
        "submission": "ELSTER-Übermittlung ist deaktiviert",
        "overview_subtitle": "Status der Steuerfälle und nächster Schritt auf einen Blick.",
        "source_connected": "● Verifizierte Quelle verbunden",
        "source_unavailable": "● Steuerfallquelle nicht verbunden",
        "connection_missing_title": "Noch keine verifizierte Verbindung",
        "connection_missing_body": "Bis der schreibgeschützte Zugriff auf die verifizierte Steuerfallquelle bestätigt ist, werden keine angenommenen Daten als echte Steuerfälle angezeigt.",
        "connection_missing_detail": "Status: Der Kernel- und Persistence-Zugriffsvertrag muss noch abgeschlossen werden.",
        "empty_title": "Keine Steuerfälle verfügbar",
        "empty_body": "Die verifizierte Quelle ist verbunden, enthält im aktuellen Berechtigungsumfang jedoch keinen Steuerfall.",
        "summary": "Steuerfallübersicht", "visible_cases": "Sichtbare Steuerfälle",
        "authorized_source": "Aus autorisierter Quelle", "latest_year": "Neuestes Steuerjahr",
        "registered_list": "In der Liste registriert", "selected_status": "Status des ausgewählten Falls",
        "verified_data": "Nach verifizierten Daten", "your_cases": "Ihre Steuerfälle",
        "case_list": "Steuerfallliste", "readonly": "Schreibgeschützt", "tax_year": "Steuerjahr",
        "next": "Nächster Schritt", "next_title": "Sichere Verbindung zu echten Steuerfällen",
        "next_body": "Nach Bestätigung der Datenquelle werden Falldetails, Dokumente und Aufgaben ohne erfundene Daten verfügbar.",
        "connection_status": "Verbindungsstatus", "secure_readonly": "Sichere Umgebung · schreibgeschützt",
        "real_unavailable": "Echte Daten sind noch nicht verfügbar",
        "real_unavailable_body": "Die autorisierte Verbindung zum dauerhaften Steuerfallregister ist in dieser Sitzung nicht bestätigt. Es werden keine irreführenden Daten erzeugt oder abgeleitet.",
        "no_case": "Im autorisierten Umfang ist kein Steuerfall vorhanden.", "case": "Steuerfall",
        "year": "Jahr", "status": "Status", "verified_case_body": "Die Steuerfallidentität stammt aus der autorisierten Quelle. Fachliche Daten dieses Bereichs werden erst nach Bestätigung des jeweiligen Zugriffsvertrags angezeigt.",
        "related_service": "Zugehöriger Dienst", "service_unverified": "Status: Die operative Verbindung dieses Bereichs ist noch nicht bestätigt.",
        "content_approval": "1. Inhaltliche Freigabe", "destination_approval": "2. Ziel- und Übermittlungsfreigabe",
        "not_recorded": "Nicht erteilt", "workspace_eyebrow": "Arbeitsbereich",
        "test_only_title": "NUR TEST · Funktionstestumgebung",
        "test_only_body": "TEST-Fälle sind keine echten Steuerfälle. Ihr Status wird aus dem lokalen Test-Backend gelesen.",
        "test_controls": "Funktionstest-Steuerung", "test_create_case": "Testfall anlegen",
        "test_case_id": "Kennung (muss mit TEST- beginnen)", "test_tax_year": "Steuerjahr",
        "test_create": "Testfall erstellen", "test_choose_case": "Testfall auswählen",
        "test_doc_register": "1. Synthetisches Dokument registrieren", "test_doc_help": "Erlaubt sind nur synthetische UTF-8-Textdateien bis 32 KB. Die Bytes bleiben ausschließlich in der lokalen Testdatenbank; es erfolgt keine externe Übertragung.",
        "test_doc_label": "Dokumenttitel", "test_doc_file": "UTF-8-Testdatei (maximal 32 KB)",
        "test_doc_submit": "Registrieren und Duplikat prüfen", "test_doc_list": "Registrierte Dokumente",
        "test_doc_empty": "Noch kein Dokument registriert.",
        "test_doc_process": "2. Nur Digest im Kernel prüfen", "test_doc_run": "Eindeutige Lauf-ID",
        "test_doc_extract": "3. Felder aus synthetischem Fixture extrahieren", "synthetic_extraction_label": "SYNTHETISCHE INHALTSEXTRAKTION — KEINE STEUERANALYSE",
        "test_doc_validate_help": "Prüft nur Dokumentbesitz und Digest; es wird kein Inhalt extrahiert.",
        "test_doc_extract_help": "Liest die Bytes im geschlossenen Fixture-Format, extrahiert Felder und öffnet anschließend direkt das Ergebnis in Analyse.",
        "test_doc_format": "Unterstützt: text/plain, UTF-8, genau sechs Zeilen DOCUMENT_TYPE, TAX_YEAR, EMPLOYER_ID, GROSS_EMPLOYMENT_INCOME, WITHHELD_WAGE_TAX und CURRENCY=EUR. PDF, Bilder, Bankdateien und echte Dokumente werden nicht unterstützt.",
        "test_doc_unavailable": "Die Kernel-Ausführung ist in diesem Launcher nicht aktiv. Öffnen Sie die Oberfläche mit dem offiziellen Test-Launcher.",
        "analysis_result_title": "Verifizierte extrahierte Felder", "analysis_find": "Nach erfolgreicher Extraktion erscheint das Ergebnis hier im Bereich Analyse.",
        "ui_errors": {"unsupported_upload": "Registrierung fehlgeschlagen: Erlaubt sind nur synthetische text/plain-Dateien bis 32 KB.", "unsupported_fixture": "Extraktion fehlgeschlagen: Das gewählte Dokument ist kein unterstütztes synthetisches Fixture oder Inhalt/Digest ist ungültig."},
        "extraction_fields": {"DOCUMENT_REFERENCE": "Dokumentreferenz", "DOCUMENT_DIGEST": "Dokument-Digest", "PARSER_SCHEMA": "Parser-Version", "EXTRACTION_DIGEST": "Extraktions-Digest", "DOCUMENT_TYPE": "Dokumenttyp", "TAX_YEAR": "Steuerjahr", "EMPLOYER_ID": "Synthetische Arbeitgeber-ID", "GROSS_EMPLOYMENT_INCOME": "Bruttoarbeitslohn", "WITHHELD_WAGE_TAX": "Einbehaltene Lohnsteuer", "CURRENCY": "Währung"},
        "kernel_title": "Echter Kernel-Status", "kernel_run": "Kernel-Lauf",
        "kernel_kill_switch": "Kill Switch", "kernel_tasks": "Registrierte Aufgaben",
        "kernel_readonly": "Dieser Status wird direkt und schreibgeschützt aus dem Kernel gelesen; die Ausführung beginnt nur durch eine ausdrückliche Benutzeraktion.",
        "kernel_execute_title": "Synthetische Kernel-Ausführung", "kernel_run_id": "Synthetische Lauf-ID",
        "kernel_value": "Synthetischer Ganzzahlwert", "kernel_execute": "Eine Testaufgabe ausführen",
        "kernel_result": "Deterministisches Worker-Ergebnis", "kernel_pending": "Unabhängige Abnahme ausstehend",
        "status_labels": {
            "CREATED": "Erstellt", "ACTIVE": "Aktiv", "PROCESSING": "In Bearbeitung",
            "REVIEW_REQUIRED": "Prüfung erforderlich", "COMPLETED": "Abgeschlossen",
            "ARCHIVED": "Archiviert", "BLOCKED": "Blockiert",
        },
        "pages": {
            "cases": ("Steuerfälle und Steuerjahr", "Steuerfälle erstellen, auswählen und öffnen", "Case Registry / CaseCreationWorkflow"),
            "family": ("Familie und Personen", "Identitäten, Familienmitglieder und kontrollierte Übernahme aus dem Vorjahr", "IdentityPersistence / CaseIdentityAssociationService"),
            "documents": ("Dokumente des Steuerfalls", "Dokumente schrittweise erfassen, Duplikate erkennen und Versionen verwalten", "Case-scoped storage / document identity"),
            "analysis": ("Analyse und Nachweise", "Extraktionsergebnisse, Agentenanalyse und Nachweisbezug jeder Feststellung", "Deterministic Kernel / Gemini extraction boundary"),
            "issues": ("Rückfragen und offene Punkte", "Nachverfolgbare Fragen und Punkte mit menschlichem Entscheidungsbedarf", "Issues / Human Gates"),
            "result": ("Berechnungsergebnis", "Versionierte Ergebnisse und Änderungsvergleich", "Deterministic tax calculation"),
            "declaration": ("Vorschau der Steuererklärung", "Formular vor der Freigabe ansehen, ohne Übermittlung", "Declaration / ERiC validation"),
            "approval": ("Freigabe und Übermittlung", "Zwei getrennte Freigaben für Inhalt und Übermittlungsziel", "Human Gate 1 / Human Gate 2"),
            "activity": ("Verlauf und Aktivitäten", "Ereignisse, Ausführungsnachweise und Prüfpfad", "Audit / Checkpoint"),
        },
    },
}


def create_dashboard_app(
    *, read_cases: ReadCases | None = None, test_store=None,
    read_kernel_projection: ReadKernelProjection | None = None,
    execute_kernel_task: ExecuteKernelTask | None = None,
) -> FastAPI:
    """Expose a fail-closed dashboard; caller must inject an authorized live resolver.

    This is not a substitute for the Kernel's permission or persistence layer.
    No fake cases, inferred 2024 status or case data are returned by default.
    """
    if test_store is not None and read_cases is not None:
        raise ValueError("test store and live case resolver must never be mixed")
    if read_kernel_projection is not None and test_store is None:
        raise ValueError("Kernel UI projection is restricted to the isolated test dashboard")
    if execute_kernel_task is not None and (test_store is None or read_kernel_projection is None):
        raise ValueError("Kernel execution requires the isolated test store and projection")
    if test_store is not None:
        read_cases = test_store.cases
    app = FastAPI(title="AI-Tax-Agent Dashboard", docs_url=None, redoc_url=None, openapi_url=None)
    templates = Jinja2Templates(directory=str(UI_ROOT / "ui_templates"))
    app.mount("/static", StaticFiles(directory=str(UI_ROOT / "ui_static")), name="static")

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        if test_store is not None and request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            host = request.headers.get("host")
            if origin != "http://127.0.0.1:8766" or host != "127.0.0.1:8766":
                from fastapi.responses import PlainTextResponse
                response = PlainTextResponse("Cross-origin mutation rejected", status_code=403)
            else:
                response = await call_next(request)
        else:
            response = await call_next(request)
        for name, value in LOCAL_SECURITY_HEADERS.items():
            response.headers[name] = value
        if test_store is not None:
            response.headers["content-security-policy"] = response.headers["content-security-policy"].replace("form-action "+chr(39)+"none"+chr(39), "form-action "+chr(39)+"self"+chr(39))
            # Chrome serializes a form POST's Origin as ``null`` when the
            # source document uses the production ``no-referrer`` policy.
            # This loopback-only app needs the browser to retain its exact
            # same-origin identity so the mutation guard can stay fail-closed.
            response.headers["referrer-policy"] = "same-origin"
        return response

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(
        request: Request, case_id: str | None = None, run_id: str | None = None,
        tab: str = "overview", lang: str = "fa-IR", error: str | None = None,
    ):
        tabs = {"overview", "cases", "family", "documents", "analysis", "issues", "result", "declaration", "approval", "activity"}
        if tab not in tabs:
            raise HTTPException(status_code=404, detail="Unknown workspace tab")
        if lang not in UI_TEXT:
            raise HTTPException(status_code=404, detail="Unsupported language")
        if error is not None and error not in UI_TEXT[lang]["ui_errors"]:
            raise HTTPException(status_code=404, detail="Unknown UI error")
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
        kernel_projection = None
        if read_kernel_projection is not None and selected is not None and tab in {"analysis", "activity"}:
            if run_id is None:
                raise HTTPException(status_code=400, detail="Exact run_id is required for Kernel status")
            try:
                kernel_projection = read_kernel_projection(selected.case_id, selected.tax_year, run_id)
            except Exception as exc:
                raise HTTPException(status_code=403, detail="Kernel scope is unavailable or unauthorized") from exc
        return templates.TemplateResponse(request=request, name="dashboard.html", context={
            "state": state, "cases": cases, "selected": selected, "tab": tab,
            "test_mode": test_store is not None, "detail": detail, "lang": lang, "t": UI_TEXT[lang],
            "run_id": run_id, "kernel_projection": kernel_projection,
            "ui_error": UI_TEXT[lang]["ui_errors"].get(error),
            "kernel_execution_available": execute_kernel_task is not None,
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
        data = await document.read(32_769)
        try:
            added = test_store.add_document(case_id, label, data, document.content_type or "")
        except ValueError:
            return RedirectResponse(
                "/?" + urlencode({"tab": "documents", "case_id": case_id, "error": "unsupported_upload"}),
                status_code=303,
            )
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

    @app.post("/test/kernel/execute")
    async def execute_test_kernel_task(
        case_id: str = Form(...), run_id: str = Form(...),
        synthetic_value: int = Form(...),
    ):
        require_test()
        if execute_kernel_task is None:
            raise HTTPException(status_code=404, detail="Synthetic Kernel execution unavailable")
        matching = tuple(item for item in test_store.cases() if item.case_id == case_id)
        if len(matching) != 1:
            raise HTTPException(status_code=400, detail="Unknown or ambiguous test case")
        try:
            execute_kernel_task(
                case_id=case_id, tax_year=matching[0].tax_year,
                run_id=run_id, synthetic_value=synthetic_value,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Synthetic Kernel execution rejected") from exc
        return RedirectResponse(
            "/?tab=analysis&case_id="+case_id+"&run_id="+run_id, status_code=303
        )

    @app.post("/test/kernel/documents/validate")
    async def validate_test_document_evidence(
        case_id: str = Form(...), run_id: str = Form(...),
        document_digest: str = Form(...),
    ):
        require_test()
        if execute_kernel_task is None:
            raise HTTPException(status_code=404, detail="Synthetic Kernel execution unavailable")
        matching = tuple(item for item in test_store.cases() if item.case_id == case_id)
        if len(matching) != 1:
            raise HTTPException(status_code=400, detail="Unknown or ambiguous test case")
        try:
            document = test_store.resolve_document(case_id, document_digest)
            execute_kernel_task(
                case_id=case_id, tax_year=matching[0].tax_year, run_id=run_id,
                document_reference=document.reference, document_digest=document.digest,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Synthetic document evidence rejected") from exc
        return RedirectResponse(
            "/?tab=analysis&case_id="+case_id+"&run_id="+run_id, status_code=303
        )

    @app.post("/test/kernel/documents/extract")
    async def extract_test_document_content(
        case_id: str = Form(...), run_id: str = Form(...),
        document_digest: str = Form(...),
    ):
        require_test()
        if execute_kernel_task is None:
            raise HTTPException(status_code=404, detail="Synthetic Kernel execution unavailable")
        matching = tuple(item for item in test_store.cases() if item.case_id == case_id)
        if len(matching) != 1:
            raise HTTPException(status_code=400, detail="Unknown or ambiguous test case")
        try:
            document = test_store.resolve_document_content(case_id, document_digest)
            execute_kernel_task(
                case_id=case_id, tax_year=matching[0].tax_year, run_id=run_id,
                document_reference=document.reference, document_digest=document.digest,
                document_content=document.content, content_type=document.content_type,
            )
        except Exception as exc:
            return RedirectResponse(
                "/?" + urlencode({"tab": "documents", "case_id": case_id, "error": "unsupported_fixture"}),
                status_code=303,
            )
        return RedirectResponse(
            "/?tab=analysis&case_id="+case_id+"&run_id="+run_id, status_code=303
        )

    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": "isolated-functional-test" if test_store is not None else "read-only-dashboard", "source": "test-only" if test_store is not None else ("configured" if read_cases else "unavailable")}

    return app
