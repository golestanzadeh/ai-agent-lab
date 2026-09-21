"""Closed Persian labels for privacy-safe synthetic UI status codes."""

STATUS_LABELS = {
    "CASE_SCOPE": "محدودهٔ پرونده",
    "DOCUMENT_INTAKE": "دریافت مدارک",
    "PROCESSING": "پردازش",
    "SPECIALIST_REVIEW": "بازبینی تخصصی",
    "CHIEF_REVIEW": "بازبینی نهایی",
    "CALCULATION": "محاسبه",
    "FORM_PREVIEW": "پیش‌نمایش فرم",
    "HUMAN_APPROVAL": "تأیید انسانی",
    "SUBMISSION": "ارسال",
    "RECEIPT": "رسید",
    "COMPLETE": "تکمیل‌شده",
    "ACTIVE": "فعال",
    "BLOCKED": "متوقف در مرز ایمنی",
    "LOCKED": "قفل‌شده",
    "READY": "آماده",
    "NOT_REQUIRED": "در حال حاضر لازم نیست",
    "REQUIRED": "نیازمند تصمیم انسانی",
    "EXPIRED": "منقضی‌شده",
    "REVOKED": "لغوشده",
    "REVIEW_SYNTHETIC_PREVIEW": "بازبینی پیش‌نمایش مصنوعی",
    "LOCAL_SYNTHETIC_PREVIEW": "پیش‌نمایش مصنوعی محلی",
    "INCOME": "درآمد",
    "EXPENSE": "هزینه",
    "OTHER": "سایر",
    "INDEXED": "فهرست‌شده",
    "REVIEW_REQUIRED": "نیازمند بازبینی",
    "CREATED": "ایجادشده",
    "PROCESSING": "در حال پردازش",
    "COMPLETED": "پایان‌یافته",
    "ARCHIVED": "بایگانی‌شده",
    "LOCAL_SYNTHETIC_RUNTIME_READY": "اجرای محلی مصنوعی آماده است",
    "LOCAL_E10_2024_XSD_AND_RULE_SUBSET_PASS": "اعتبارسنجی محلی E10 و قواعد منتخب موفق است",
    "OFFICIAL_ERIC_ENGINE_NOT_EXECUTED": "موتور رسمی ERiC اجرا نشده است",
    "PRODUCTION_SUBMISSION_PATH_NOT_AUTHORIZED": "مسیر ارسال واقعی مجاز نیست",
    "READ_ONLY_RECOVERY_DIAGNOSTICS_AVAILABLE": "گزارش فقط‌خواندنی بازیابی در دسترس است",
    "PAUSE_CONTROL_NOT_IMPLEMENTED": "کنترل توقف موقت پیاده‌سازی نشده است",
    "RESUME_CONTROL_NOT_IMPLEMENTED": "کنترل ادامه پیاده‌سازی نشده است",
    "STOP_CONTROL_NOT_IMPLEMENTED": "کنترل توقف کامل پیاده‌سازی نشده است",
    "RECEIPT_NOT_AVAILABLE_NO_TRANSMISSION": "چون ارسالی انجام نشده، رسیدی وجود ندارد",
    "NOT_APPROVED": "تأیید نشده است",
    "NOT_EXECUTED": "اجرا نشده است",
    "LOCAL_MAPPING_XSD_AND_RULE_SUBSET_PASS": "نگاشت، XSD و قواعد منتخب محلی موفق‌اند",
    "OFFICIAL_ERIC_PLAUSIBILITY_ENGINE_NOT_EXECUTED": "موتور رسمی کنترل ERiC اجرا نشده است",
    "REAL_PAYLOAD_NOT_AUTHORIZED": "دادهٔ واقعی مجاز نیست",
    "ARTICLE_1_CONTENT_RELEASE_NOT_APPROVED": "مجوز محتوای مادهٔ ۱ صادر نشده است",
    "ARTICLE_1_DESTINATION_TRANSMISSION_NOT_APPROVED": "مجوز مقصد و ارسال مادهٔ ۱ صادر نشده است",
    "TRANSMITTER_NOT_IMPLEMENTED": "فرستنده پیاده‌سازی نشده است",
    "LOCAL_E10_2024_XSD_VALIDATED": "ساختار محلی E10/2024 با XSD معتبر است",
    "LOCAL_SIX_RULE_SUBSET_PASS": "شش قاعدهٔ محلی منتخب موفق‌اند",
    "SYNTH_INCOME_REVIEWED": "درآمد مصنوعی بازبینی شده است",
    "SYNTH_EXPENSE_REVIEWED": "هزینهٔ مصنوعی بازبینی شده است",
}


class UIStatusLabelError(ValueError):
    pass


def persian_status_label(code: str) -> str:
    if not isinstance(code, str) or code not in STATUS_LABELS:
        raise UIStatusLabelError("unknown UI status code")
    return STATUS_LABELS[code]
