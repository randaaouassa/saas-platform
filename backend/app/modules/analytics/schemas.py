from datetime import date

from pydantic import BaseModel


class OrdersSummary(BaseModel):
    date: date
    orders_count: int
    delivered_count: int
    cancelled_count: int
    revenue: float


class DeliveriesSummary(BaseModel):
    date: date
    deliveries_count: int
    delivered_count: int
    failed_count: int
    success_rate: float
    avg_duration_s: float | None


class DriverSummary(BaseModel):
    driver_id: str
    deliveries_count: int
    delivered_count: int
    distance_m: float


class InventorySummary(BaseModel):
    product_id: str
    warehouse_id: str
    on_hand: float
    reserved: float
    low_stock: bool


class OverviewResponse(BaseModel):
    orders: OrdersSummary | None
    deliveries: DeliveriesSummary | None
    drivers: list[DriverSummary]
    inventory: list[InventorySummary]


class RebuildResponse(BaseModel):
    date: date
    orders_rows: int
    deliveries_rows: int
    driver_rows: int
    inventory_rows: int


class RangeOrdersItem(BaseModel):
    date: date
    orders_count: int
    delivered_count: int
    cancelled_count: int
    revenue: float


class RangeDeliveriesItem(BaseModel):
    date: date
    deliveries_count: int
    delivered_count: int
    failed_count: int
    success_rate: float


class RangeResponse(BaseModel):
    from_date: date
    to_date: date
    orders: list[RangeOrdersItem]
    deliveries: list[RangeDeliveriesItem]
    total_revenue: float
    total_orders: int
    total_deliveries: int
    total_delivered: int
    total_failed: int
    avg_delivery_time_s: float | None
    top_products: list[dict]


class AvgDeliveryTimeResponse(BaseModel):
    from_date: date
    to_date: date
    avg_duration_s: float | None
    sample_count: int