from bi.profiles.base import BIConfig, IndustryProfile, ProfileData
from bi.profiles.helpers import rules

PROFILE = IndustryProfile(
    id="retail_ecommerce", name="Retail / E-commerce", description="Ventas de productos, pedidos y clientes.",
    data=ProfileData(
        fields=rules(["date", "amount"], ["transaction_id", "concept", "quantity"], ["customer_id", "customer_name", "category", "subcategory", "unit_price", "cost", "discount", "channel", "location", "responsible", "status", "currency"]),
        aliases={
            "date": ["fecha", "fecha_venta", "fecha_compra", "order_date", "fecha_pedido"], "transaction_id": ["pedido", "pedido_id", "order_id", "factura", "nro_factura", "numero_factura", "ticket"],
            "concept": ["producto", "articulo", "item", "product", "sku", "descripcion"], "category": ["categoria", "rubro", "familia"], "quantity": ["cantidad", "cant", "qty", "units", "unidades"],
            "unit_price": ["precio", "precio_unitario"], "amount": ["importe", "total", "venta", "ventas", "valor_total", "total_venta", "revenue"], "cost": ["costo", "coste", "costo_total"],
            "channel": ["canal", "origen"], "location": ["provincia", "region", "zona", "ubicacion", "sucursal"], "responsible": ["vendedor", "salesperson", "asesor"],
            "customer_id": ["cliente_id", "id_cliente"], "customer_name": ["cliente", "customer", "nombre_cliente"],
        }, terminology={"es": {"concept": "Producto", "responsible": "Vendedor", "amount": "Venta"}},
    ), bi=BIConfig(featured_dimensions=("category", "channel", "concept", "location"), extra_filters=("channel", "category", "location")),
)
