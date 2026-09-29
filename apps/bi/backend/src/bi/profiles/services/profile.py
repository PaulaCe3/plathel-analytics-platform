from bi.profiles.base import IndustryProfile, ProfileData
from bi.profiles.helpers import extension, rules

PROFILE = IndustryProfile(
    id="services", name="Servicios", description="Prestaciones, profesionales, proyectos y facturación.",
    data=ProfileData(
        fields=rules(["date", "amount"], ["concept", "responsible", "customer_name"], ["transaction_id", "customer_id", "category", "channel", "location", "status", "currency", "duration_hours", "project"]),
        extension_fields=(extension("duration_hours", "measure", "decimal"), extension("project", "dimension", "string")),
        aliases={"date": ["fecha", "fecha_servicio", "service_date"], "concept": ["servicio", "tipo_servicio", "service", "prestacion"], "responsible": ["profesional", "consultor", "tecnico", "especialista"], "amount": ["importe", "total", "facturacion", "honorarios"], "duration_hours": ["duracion", "duracion_horas", "horas", "horas_facturadas"], "project": ["proyecto"], "customer_name": ["cliente", "empresa", "customer"]},
        terminology={"es": {"concept": "Servicio", "responsible": "Profesional", "amount": "Facturación"}},
    ),
)
