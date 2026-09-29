from bi.profiles.base import IndustryProfile, ProfileData
from bi.profiles.helpers import extension, rules

PROFILE = IndustryProfile(
    id="hospitality", name="Hotelería", description="Reservas, estadías, habitaciones e ingresos.",
    data=ProfileData(
        fields=rules(["check_in", "amount"], ["transaction_id", "room_type", "nights"], ["booking_date", "check_out", "guests", "customer_name", "channel", "location", "status", "currency"]),
        extension_fields=(extension("booking_date", "time", "date"), extension("check_in", "time", "date"), extension("check_out", "time", "date"), extension("nights", "measure", "integer"), extension("room_type", "dimension", "string"), extension("guests", "measure", "integer")),
        aliases={"booking_date": ["fecha_reserva", "reservation_date"], "check_in": ["checkin", "entrada", "fecha_entrada"], "check_out": ["checkout", "salida", "fecha_salida"], "nights": ["noches"], "room_type": ["habitacion", "tipo_habitacion", "room"], "guests": ["huespedes", "pasajeros"], "amount": ["importe", "total", "ingreso", "revenue", "tarifa_total"], "channel": ["canal", "booking_channel", "origen_reserva"], "transaction_id": ["reserva", "reserva_id", "booking_id", "reservation_id"]},
        terminology={"es": {"concept": "Habitación", "amount": "Ingreso", "responsible": "Responsable"}}, primary_date="check_in", alternate_dates=("booking_date",),
    ),
)
