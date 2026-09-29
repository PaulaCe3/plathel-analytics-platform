from analytics_core.canonical.fields import UNIVERSAL_FIELDS, FieldSpec
from analytics_core.ingestion.models import ColumnMetadata
from analytics_core.mapping.matcher import suggest_mappings
from analytics_core.mapping.models import ColumnDisposition, ColumnMapping
from analytics_core.mapping.validation import validate_mapping
from bi.profiles import get_profile, list_profiles
from bi.profiles.base import IndustryProfile, ProfileData, ProfileFieldRule
from bi.profiles.registry import profile_fields, register_profile


def column(key: str, name: str, samples: list[str]) -> ColumnMetadata:
    return ColumnMetadata(key=key, original_name=name, sample=samples, approximate_cardinality=len(set(samples)))


def test_universal_catalog_is_unique_and_declarative() -> None:
    assert len({field.id for field in UNIVERSAL_FIELDS}) == len(UNIVERSAL_FIELDS)
    assert all(field.kind in {"identifier", "dimension", "measure", "time"} for field in UNIVERSAL_FIELDS)
    assert all(field.dtype in {"string", "integer", "decimal", "date", "datetime", "boolean"} for field in UNIVERSAL_FIELDS)
    assert not hasattr(UNIVERSAL_FIELDS[0], "required")


def test_builtin_profiles_are_valid() -> None:
    profiles = list_profiles()
    assert {profile.id for profile in profiles} == {"custom", "retail_ecommerce", "services", "hospitality"}
    for profile in profiles:
        fields = {field.id for field in profile_fields(profile)}
        assert profile.data.primary_date in fields
        assert set(profile.data.alternate_dates) <= fields
        assert {rule.level for rule in profile.data.fields} <= {"required", "recommended", "optional"}


def test_matcher_aliases_are_deterministic() -> None:
    cases = {
        "retail_ecommerce": [("fecha_compra", "date", ["2026-01-01"]), ("nro_factura", "transaction_id", ["F1"]), ("articulo", "concept", ["Mate"]), ("cant", "quantity", ["2"]), ("valor_total", "amount", ["100.5"])],
        "services": [("tipo_servicio", "concept", ["Consulta"]), ("profesional", "responsible", ["Ana"]), ("facturacion", "amount", ["2500"])],
        "hospitality": [("check_in", "check_in", ["2026-01-01"]), ("fecha_reserva", "booking_date", ["2025-12-01"]), ("tipo_habitacion", "room_type", ["Doble"])],
    }
    for profile_id, examples in cases.items():
        profile = get_profile(profile_id)
        for index, (header, expected, samples) in enumerate(examples, start=1):
            suggestion = suggest_mappings([column(f"c{index:02d}", header, samples)], profile_fields(profile), profile.data.aliases)[0]
            assert suggestion.candidates[0].field_id == expected
            assert suggestion.candidates[0].reasons


def test_conflicts_and_custom_limits() -> None:
    profile = get_profile("retail_ecommerce")
    columns = [column("c01", "fecha", ["no-es-fecha"]), column("c02", "importe", ["texto"]), column("c03", "otra", ["x"])]
    mappings = [ColumnMapping(column_key="c01", target_field="date", disposition="canonical"), ColumnMapping(column_key="c02", target_field="amount", disposition="canonical"), ColumnMapping(column_key="c03", target_field="amount", disposition="canonical")]
    conflicts = validate_mapping(mappings, columns, profile_fields(profile), {"date", "amount"}, max_custom_dimensions=0, max_custom_measures=0)
    assert {item.code for item in conflicts} >= {"TIME_INCOMPATIBLE", "MEASURE_INCOMPATIBLE", "DUPLICATE_TARGET"}
    custom = [ColumnMapping(column_key="c03", disposition=ColumnDisposition.custom_dimension)]
    conflicts = validate_mapping(custom, columns, profile_fields(profile), set(), max_custom_dimensions=0, max_custom_measures=0)
    assert conflicts[0].code == "CUSTOM_DIMENSION_LIMIT"
    custom_measure = [ColumnMapping(column_key="c03", disposition=ColumnDisposition.custom_measure)]
    conflicts = validate_mapping(custom_measure, columns, profile_fields(profile), set(), max_custom_dimensions=10, max_custom_measures=0)
    assert conflicts[0].code == "CUSTOM_MEASURE_LIMIT"
    ignored = ColumnMapping(column_key="c03", disposition=ColumnDisposition.ignored)
    assert ignored.target_field is None


def test_runtime_synthetic_profile_uses_unchanged_core() -> None:
    profile = IndustryProfile(id="_test_industry", name="Test", description="Synthetic", data=ProfileData(fields=(ProfileFieldRule(field_id="amount", level="required"), ProfileFieldRule(field_id="date", level="optional")), aliases={"amount": ["creditos_magicos"]}, primary_date="date"))
    register_profile(profile)
    suggestion = suggest_mappings([column("c01", "creditos_magicos", ["42"])], profile_fields(profile), profile.data.aliases)[0]
    assert suggestion.candidates[0].field_id == "amount"
