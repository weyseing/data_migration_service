from backend.mapping.ai_mapper import map_all_procedures
from backend.mapping.type_mapper import map_all_tables
from backend.models.discovery import DiscoveryResult
from backend.models.mapping import MappingResult


def run_mapping(discovery: DiscoveryResult) -> MappingResult:
    table_mappings = map_all_tables(discovery.tables)
    procedure_mappings = map_all_procedures(discovery.stored_procedures)
    return MappingResult(
        table_mappings=table_mappings,
        procedure_mappings=procedure_mappings,
    )
