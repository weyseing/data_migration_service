import anthropic

from backend.config import ANTHROPIC_API_KEY
from backend.models.mapping import ProcedureMapping
from backend.models.refactoring import ProcedureRefactor

MODEL = "claude-haiku-4-5-20251001"


def refactor_procedure(pm: ProcedureMapping) -> ProcedureRefactor:
    """Use Claude to refactor a mapped procedure into modern, optimised PostgreSQL."""
    # If the mapping step already failed or was skipped, carry it through
    if pm.target_sql.startswith("-- Skipped"):
        return ProcedureRefactor(
            source_name=pm.source_name,
            source_body=pm.source_body,
            target_sql=pm.target_sql,
            explanation="Skipped: no mapping available",
        )

    if not ANTHROPIC_API_KEY:
        return ProcedureRefactor(
            source_name=pm.source_name,
            source_body=pm.source_body,
            target_sql=pm.target_sql,
            explanation="No API key configured. Using mapping output as-is.",
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Refactor this PostgreSQL function for correctness and modern best practices.

Rules:
- Replace cursor loops with set-based operations (INSERT ... SELECT, CTEs) where possible
- Use RETURNS TABLE or RETURNS SETOF for multi-row returns
- Add explicit parameter types if missing
- Ensure correct PL/pgSQL syntax (dollar-quoting, DECLARE block, etc.)
- Preserve the original logic and output
- Return ONLY the final PostgreSQL function SQL, no explanation

Current PostgreSQL function (converted from MySQL):
{pm.target_sql}

Original MySQL procedure for reference:
{pm.source_body}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    target_sql = message.content[0].text.strip()

    # Remove markdown fences if present
    if target_sql.startswith("```"):
        lines = target_sql.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        target_sql = "\n".join(lines).strip()

    return ProcedureRefactor(
        source_name=pm.source_name,
        source_body=pm.source_body,
        target_sql=target_sql,
        explanation=f"Refactored by {MODEL} — cursor loops replaced with set-based SQL",
    )


def refactor_all_procedures(
    procedure_mappings: list[ProcedureMapping],
) -> list[ProcedureRefactor]:
    """Refactor all mapped procedures."""
    return [refactor_procedure(pm) for pm in procedure_mappings]
