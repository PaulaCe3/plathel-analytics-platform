from bi.profiles.base import BIConfig, BIWidgetConfig, IndustryProfile, ProfileData
from bi.profiles.helpers import extension, rules

PROFILE = IndustryProfile(
    id="services", name="Servicios", description="Prestaciones, profesionales, proyectos y facturación.",
    data=ProfileData(
        fields=rules(["date", "amount"], ["concept", "responsible", "customer_name"], ["transaction_id", "customer_id", "category", "channel", "location", "status", "currency", "duration_hours", "project"]),
        extension_fields=(extension("duration_hours", "measure", "decimal"), extension("project", "dimension", "string")),
        aliases={"date": ["fecha", "fecha_servicio", "service_date"], "concept": ["servicio", "tipo_servicio", "service", "prestacion"], "responsible": ["profesional", "consultor", "tecnico", "especialista"], "amount": ["importe", "total", "facturacion", "honorarios"], "duration_hours": ["duracion", "duracion_horas", "horas", "horas_facturadas"], "project": ["proyecto"], "customer_name": ["cliente", "empresa", "customer"]},
        terminology={"es": {"concept": "Servicio", "responsible": "Profesional", "amount": "Facturación"}},
    ), bi=BIConfig(metrics=('revenue', 'transactions', 'customers', 'avg_transaction_value', 'quantity', 'avg_unit_price', 'service_hours', 'revenue_per_hour'), kpi_order=('revenue', 'transactions', 'service_hours', 'revenue_per_hour', 'customers'), featured_dimensions=('responsible', 'concept', 'customer_name', 'project'), extra_filters=('concept', 'responsible', 'customer_name', 'project'), widgets=(BIWidgetConfig(id="service_hours_by_project", type="breakdown", title_key="metric.service_hours", metric_id="service_hours", dimension="project", top_n=10), BIWidgetConfig(id="revenue_per_hour_by_concept", type="breakdown", title_key="metric.revenue_per_hour", metric_id="revenue_per_hour", dimension="concept", top_n=10), BIWidgetConfig(id="revenue_by_responsible", type="breakdown", title_key="metric.revenue", metric_id="revenue", dimension="responsible", top_n=10),), insight_rules=BIConfig().insight_rules + ("industry_leader",)),
)
