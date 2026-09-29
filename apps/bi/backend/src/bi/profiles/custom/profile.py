from bi.profiles.base import BIConfig, IndustryProfile, ProfileData
from bi.profiles.helpers import rules

PROFILE = IndustryProfile(
    id="custom", name="Personalizado", description="Perfil genérico para datos de cualquier actividad.",
    data=ProfileData(
        fields=rules(["amount"], ["date", "concept"], ["transaction_id", "customer_id", "customer_name", "category", "quantity", "channel", "location", "responsible", "status", "currency"]),
        aliases={"date": ["fecha"], "amount": ["importe", "total", "monto"], "concept": ["concepto", "descripcion"], "customer_name": ["cliente"], "transaction_id": ["operacion_id", "id"]},
        terminology={"es": {"concept": "Concepto", "responsible": "Responsable", "amount": "Importe"}},
    ), bi=BIConfig(),
)
