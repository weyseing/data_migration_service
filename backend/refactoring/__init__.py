from backend.models.discovery import DiscoveryResult
from backend.models.mapping import MappingResult
from backend.models.refactoring import RefactoringResult
from backend.refactoring.ai_refactor import refactor_all_procedures
from backend.refactoring.ddl_generator import generate_all_ddl
from backend.refactoring.validator import validate_all


def run_refactoring(
    discovery: DiscoveryResult,
    mapping: MappingResult,
) -> RefactoringResult:
    # Generate CREATE TABLE DDL from discovery schema + mapped types
    table_ddls = generate_all_ddl(discovery, mapping.table_mappings)

    # Refactor stored procedures via AI (improve the mapping output)
    procedure_refactors = refactor_all_procedures(mapping.procedure_mappings)

    # Validate everything against the target PostgreSQL database
    table_ddls, procedure_refactors = validate_all(table_ddls, procedure_refactors, discovery)

    return RefactoringResult(
        table_ddls=table_ddls,
        procedure_refactors=procedure_refactors,
    )
