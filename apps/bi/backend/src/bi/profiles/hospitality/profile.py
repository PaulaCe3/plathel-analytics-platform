from bi.profiles.base import BIConfig, BIWidgetConfig, IndustryProfile, ProfileData
from bi.profiles.helpers import extension, rules
from analytics_core.validation.models import ProfileCheck

PROFILE = IndustryProfile(
    id="hospitality", name="Hotelería", description="Reservas, estadías, habitaciones e ingresos.",
    data=ProfileData(
        fields=rules(["check_in", "amount"], ["transaction_id", "room_type", "nights"], ["booking_date", "check_out", "guests", "customer_name", "channel", "location", "status", "currency"]),
        extension_fields=(extension("booking_date", "time", "date"), extension("check_in", "time", "date"), extension("check_out", "time", "date"), extension("nights", "measure", "integer"), extension("room_type", "dimension", "string"), extension("guests", "measure", "integer")),
        aliases={"booking_date": ["fecha_reserva", "reservation_date"], "check_in": ["checkin", "entrada", "fecha_entrada"], "check_out": ["checkout", "salida", "fecha_salida"], "nights": ["noches"], "room_type": ["habitacion", "tipo_habitacion", "room"], "guests": ["huespedes", "pasajeros"], "amount": ["importe", "total", "ingreso", "revenue", "tarifa_total"], "channel": ["canal", "booking_channel", "origen_reserva"], "transaction_id": ["reserva", "reserva_id", "booking_id", "reservation_id"]},
        terminology={"es": {"concept": "Habitación", "amount": "Ingreso", "responsible": "Responsable"}}, primary_date="check_in", alternate_dates=("booking_date",),
        checks=(ProfileCheck(id="checkout_after_checkin", operation="greater_than", left_field="check_out", right_field="check_in", severity="warning", message="La fecha de salida debe ser posterior a la fecha de entrada."),),
    ), bi=BIConfig(metrics=('revenue', 'transactions', 'customers', 'avg_transaction_value', 'quantity', 'avg_unit_price', 'total_nights', 'adr', 'average_stay'), kpi_order=('revenue', 'transactions', 'total_nights', 'adr', 'average_stay'), featured_dimensions=('room_type', 'channel', 'location'), extra_filters=('room_type', 'channel', 'location'), widgets=(BIWidgetConfig(id="adr_by_room_type", type="breakdown", title_key="metric.adr", metric_id="adr", dimension="room_type", top_n=10), BIWidgetConfig(id="total_nights_by_channel", type="breakdown", title_key="metric.total_nights", metric_id="total_nights", dimension="channel", top_n=10), BIWidgetConfig(id="average_stay_by_room_type", type="breakdown", title_key="metric.average_stay", metric_id="average_stay", dimension="room_type", top_n=10),), insight_rules=BIConfig().insight_rules + ("industry_leader",)),
)
