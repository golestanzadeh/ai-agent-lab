from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from google import genai

from agent_lab.tax_agent_runtime import ChiefTaxAuditOrchestrator, GeminiTaxAgentBackend


def _load_env_file(path: Path) -> None:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "GEMINI_API_KEY" and value.strip():
            os.environ.setdefault("GEMINI_API_KEY", value.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the case-scoped tax multi-agent pipeline")
    parser.add_argument("--case-packet", required=True, type=Path)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--model", default="gemini-3.8-flash")
    parser.add_argument("--goal", default="Audit the case for missed or incorrect German tax treatment")
    args = parser.parse_args()

    if args.env_file:
        _load_env_file(args.env_file)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is required; keep it outside the repository")

    packet = json.loads(args.case_packet.read_text(encoding="utf-8"))
    case_id = str(packet["case_id"])
    tax_year = int(packet["tax_year"])

    client = genai.Client(api_key=api_key)
    runtime = ChiefTaxAuditOrchestrator(GeminiTaxAgentBackend(client, model=args.model))
    chief_result = runtime.run(case_id=case_id, tax_year=tax_year, goal=args.goal, case_packet=packet)
    result = chief_result.specialist_run

    output = {
        "case_id": result.case_id,
        "tax_year": result.tax_year,
        "status": chief_result.status.value,
        "chief": {
            "role": chief_result.chief_report.role.value,
            "status": chief_result.chief_report.status.value,
            "summary": chief_result.chief_report.summary,
            "evidence_gaps": list(chief_result.chief_report.evidence_gaps),
            "challenges": list(chief_result.chief_report.challenges),
            "next_action": chief_result.chief_report.next_action,
        },
        "reports": [
            {
                "role": report.role.value,
                "status": report.status.value,
                "summary": report.summary,
                "findings": [
                    {
                        "finding_id": finding.finding_id,
                        "title": finding.title,
                        "status": finding.status.value,
                        "amount_eur": finding.amount_eur,
                        "tax_effect_eur": finding.tax_effect_eur,
                        "evidence_refs": list(finding.evidence_refs),
                        "legal_refs": list(finding.legal_refs),
                        "form_refs": list(finding.form_refs),
                        "rationale": finding.rationale,
                    }
                    for finding in report.findings
                ],
                "evidence_gaps": list(report.evidence_gaps),
                "challenges": list(report.challenges),
                "next_action": report.next_action,
            }
            for report in result.reports
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
