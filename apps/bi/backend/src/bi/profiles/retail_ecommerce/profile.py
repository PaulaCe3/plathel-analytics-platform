from bi.profiles.base import BIConfig, BIWidgetConfig, IndustryProfile, ProfileData
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
    ), bi=BIConfig(metrics=('revenue', 'transactions', 'customers', 'avg_transaction_value', 'quantity', 'avg_unit_price', 'units_sold', 'total_cost', 'gross_profit', 'gross_margin_pct', 'average_discount'), kpi_order=('revenue', 'gross_profit', 'gross_margin_pct', 'transactions', 'units_sold'), featured_dimensions=('category', 'channel', 'concept', 'location'), extra_filters=('category', 'channel', 'concept', 'location'), widgets=(BIWidgetConfig(id="gross_profit_by_category", type="breakdown", title_key="metric.gross_profit", metric_id="gross_profit", dimension="category", top_n=10), BIWidgetConfig(id="units_sold_by_concept", type="breakdown", title_key="metric.units_sold", metric_id="units_sold", dimension="concept", top_n=10), BIWidgetConfig(id="average_discount_by_channel", type="breakdown", title_key="metric.average_discount", metric_id="average_discount", dimension="channel", top_n=10),), insight_rules=BIConfig().insight_rules + ("industry_leader",)),
)
