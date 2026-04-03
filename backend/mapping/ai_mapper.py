import anthropic

from backend.config import ANTHROPIC_API_KEY
from backend.models.discovery import StoredProcedure
from backend.models.mapping import ProcedureMapping

MODEL = "claude-haiku-4-5-20251001"


def map_procedure(proc: StoredProcedure) -> ProcedureMapping:
    """Use Claude Haiku to rewrite a MySQL stored procedure to PostgreSQL."""
    if not ANTHROPIC_API_KEY:
        return ProcedureMapping(
            source_name=proc.name,
            source_body=proc.body,
            target_sql="-- Skipped: ANTHROPIC_API_KEY not set",
            explanation="No API key configured. Set ANTHROPIC_API_KEY to enable AI mapping.",
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Convert this MySQL stored procedure to a PostgreSQL function.

Rules:
- Use PL/pgSQL (CREATE OR REPLACE FUNCTION ... RETURNS ... LANGUAGE plpgsql)
- Replace MySQL cursors with PostgreSQL equivalents or set-based operations
- Replace TEMPORARY TABLE with PostgreSQL temp tables if needed
- Keep the same logic and output
- Return ONLY the PostgreSQL function SQL, no explanation

MySQL procedure:
{proc.body}"""

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

    return ProcedureMapping(
        source_name=proc.name,
        source_body=proc.body,
        target_sql=target_sql,
        explanation=f"Converted by {MODEL}",
    )


def map_all_procedures(procs: list[StoredProcedure]) -> list[ProcedureMapping]:
    """Map all stored procedures."""
    return [map_procedure(p) for p in procs]
