import math
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.audit import record
from app.core.errors import ConflictError, NotFoundError, ValidationError_
from app.core.uow import UnitOfWork
from app.modules.deliveries.models import Delivery
from app.modules.drivers.models import Driver
from app.modules.routing.models import Route, RouteRecalculation, RouteStop

DEFAULT_SPEED_KMH = 30.0
STOP_SERVICE_SECONDS = 300
ROUTE_STATUSES = {"planned", "active", "completed", "cancelled"}
STOP_STATUSES = {"pending", "arrived", "completed", "skipped", "failed"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _nearest_neighbor_order(
    start: tuple[float, float] | None, points: list[tuple[float, float]]
) -> list[int]:
    if not points:
        return []
    n = len(points)
    visited = [False] * n
    order: list[int] = []
    cur = start if start else points[0]
    for _ in range(n):
        best = -1
        best_d = float("inf")
        for i in range(n):
            if visited[i]:
                continue
            d = _haversine_km(cur[0], cur[1], points[i][0], points[i][1])
            if d < best_d:
                best_d = d
                best = i
        visited[best] = True
        order.append(best)
        cur = points[best]
    return order


def _recalc_totals(db, route: Route) -> None:
    stops = sorted(route.stops, key=lambda s: s.sequence)
    cur: tuple[float, float] | None = None
    total_m = 0.0
    total_s = 0.0
    eta = _now()

    for s in stops:
        d = db.scalar(select(Delivery).where(Delivery.id == s.delivery_id))
        if not d:
            continue
        coord = (
            (d.dropoff_lat, d.dropoff_lng)
            if d.dropoff_lat is not None and d.dropoff_lng is not None
            else (0.0, 0.0)
        )
        if cur is not None:
            leg_km = _haversine_km(cur[0], cur[1], coord[0], coord[1])
        else:
            leg_km = 0.0
        leg_s = (leg_km / DEFAULT_SPEED_KMH) * 3600.0
        total_m += leg_km * 1000.0
        total_s += leg_s + STOP_SERVICE_SECONDS
        eta = eta + timedelta(seconds=leg_s)
        s.eta = eta
        cur = coord

    route.total_distance_m = Decimal(str(round(total_m, 2)))
    route.total_duration_s = Decimal(str(round(total_s, 2)))


def create_route(
    uow: UnitOfWork,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    driver_id: uuid.UUID,
    route_date: date,
    delivery_ids: list[uuid.UUID],
) -> Route:
    db = uow.session

    driver = db.scalar(
        select(Driver).where(Driver.id == driver_id, Driver.organization_id == org_id)
    )
    if not driver:
        raise NotFoundError("driver not found")

    deliveries: list[Delivery] = []
    for did in delivery_ids:
        d = db.scalar(
            select(Delivery).where(Delivery.id == did, Delivery.organization_id == org_id)
        )
        if not d:
            raise NotFoundError(f"delivery not found: {did}")
        if d.status not in {"pending", "assigned", "rescheduled"}:
            raise ConflictError(f"delivery {did} not routable in status {d.status}")
        deliveries.append(d)

    start: tuple[float, float] | None = None
    for d in deliveries:
        if d.pickup_lat is not None and d.pickup_lng is not None:
            start = (d.pickup_lat, d.pickup_lng)
            break

    coords: list[tuple[float, float]] = []
    for d in deliveries:
        if d.dropoff_lat is None or d.dropoff_lng is None:
            coords.append((0.0, 0.0))
        else:
            coords.append((d.dropoff_lat, d.dropoff_lng))

    order = _nearest_neighbor_order(start, coords)
    ordered = [deliveries[i] for i in order]

    route = Route(
        organization_id=org_id,
        driver_id=driver_id,
        date=route_date,
        status="planned",
    )
    db.add(route)
    uow.flush()

    for seq, d in enumerate(ordered, start=1):
        db.add(
            RouteStop(
                organization_id=org_id,
                route_id=route.id,
                delivery_id=d.id,
                sequence=seq,
                status="pending",
            )
        )
    uow.flush()
    db.refresh(route)
    _recalc_totals(db, route)

    record(db, organization_id=org_id, actor_id=actor_id,
           action="route.created", resource="route", resource_id=str(route.id))
    uow.commit()
    db.refresh(route)
    return route


def list_routes(
    uow: UnitOfWork, org_id: uuid.UUID, driver_id: uuid.UUID | None = None
) -> list[Route]:
    q = select(Route).where(Route.organization_id == org_id)
    if driver_id:
        q = q.where(Route.driver_id == driver_id)
    return list(uow.session.scalars(q.order_by(Route.date.desc())))


def get_route(uow: UnitOfWork, org_id: uuid.UUID, route_id: uuid.UUID) -> Route:
    r = uow.session.scalar(
        select(Route).where(Route.id == route_id, Route.organization_id == org_id)
    )
    if not r:
        raise NotFoundError("route not found")
    return r


def update_route_status(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, route_id: uuid.UUID, status: str
) -> Route:
    if status not in ROUTE_STATUSES:
        raise ValidationError_(f"invalid route status: {status}")
    r = get_route(uow, org_id, route_id)
    r.status = status
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action=f"route.{status}", resource="route", resource_id=str(r.id))
    uow.commit()
    uow.session.refresh(r)
    return r


def start_route(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, route_id: uuid.UUID
) -> Route:
    return update_route_status(uow, org_id, actor_id, route_id, "active")


def complete_route(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, route_id: uuid.UUID
) -> Route:
    return update_route_status(uow, org_id, actor_id, route_id, "completed")


def delete_route(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, route_id: uuid.UUID
) -> None:
    r = get_route(uow, org_id, route_id)
    if r.status == "active":
        raise ConflictError("cannot delete an active route")
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action="route.deleted", resource="route", resource_id=str(r.id))
    uow.session.delete(r)
    uow.commit()


def add_stop(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    route_id: uuid.UUID, delivery_id: uuid.UUID, position: int | None = None,
) -> Route:
    db = uow.session
    route = get_route(uow, org_id, route_id)
    if route.status != "planned":
        raise ConflictError(f"cannot add stop to route in status {route.status}")

    d = db.scalar(
        select(Delivery).where(Delivery.id == delivery_id, Delivery.organization_id == org_id)
    )
    if not d:
        raise NotFoundError("delivery not found")

    exists = db.scalar(
        select(RouteStop).where(
            RouteStop.route_id == route.id, RouteStop.delivery_id == delivery_id
        )
    )
    if exists:
        raise ConflictError("delivery already in route")

    stops = sorted(route.stops, key=lambda s: s.sequence)
    pos = position if position else len(stops) + 1
    pos = max(1, min(pos, len(stops) + 1))

    for s in stops:
        if s.sequence >= pos:
            s.sequence += 1

    db.add(
        RouteStop(
            organization_id=org_id,
            route_id=route.id,
            delivery_id=delivery_id,
            sequence=pos,
            status="pending",
        )
    )
    uow.flush()
    db.refresh(route)
    _recalc_totals(db, route)
    record(db, organization_id=org_id, actor_id=actor_id,
           action="route.stop_added", resource="route", resource_id=str(route.id))
    uow.commit()
    db.refresh(route)
    return route


def remove_stop(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID,
    route_id: uuid.UUID, stop_id: uuid.UUID,
) -> Route:
    db = uow.session
    route = get_route(uow, org_id, route_id)
    if route.status != "planned":
        raise ConflictError(f"cannot remove stop from route in status {route.status}")

    stop = db.scalar(
        select(RouteStop).where(RouteStop.id == stop_id, RouteStop.route_id == route.id)
    )
    if not stop:
        raise NotFoundError("stop not found")

    removed_seq = stop.sequence
    db.delete(stop)
    for s in route.stops:
        if s.sequence > removed_seq:
            s.sequence -= 1
    uow.flush()
    db.refresh(route)
    _recalc_totals(db, route)
    record(db, organization_id=org_id, actor_id=actor_id,
           action="route.stop_removed", resource="route", resource_id=str(route.id))
    uow.commit()
    db.refresh(route)
    return route


def update_stop_status(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, stop_id: uuid.UUID, status: str
) -> RouteStop:
    if status not in STOP_STATUSES:
        raise ValidationError_(f"invalid stop status: {status}")
    s = uow.session.scalar(
        select(RouteStop).where(RouteStop.id == stop_id, RouteStop.organization_id == org_id)
    )
    if not s:
        raise NotFoundError("stop not found")
    s.status = status
    if status == "arrived" and s.arrived_at is None:
        s.arrived_at = _now()
    if status in {"completed", "skipped", "failed"} and s.departed_at is None:
        s.departed_at = _now()
    record(uow.session, organization_id=org_id, actor_id=actor_id,
           action=f"route_stop.{status}", resource="route_stop", resource_id=str(s.id))
    uow.commit()
    uow.session.refresh(s)
    return s


def recalculate(
    uow: UnitOfWork, org_id: uuid.UUID, actor_id: uuid.UUID, route_id: uuid.UUID, reason: str
) -> Route:
    db = uow.session
    route = get_route(uow, org_id, route_id)

    before = {
        "stops": [
            {"id": str(s.id), "delivery_id": str(s.delivery_id), "sequence": s.sequence}
            for s in route.stops
        ]
    }

    pending = [s for s in route.stops if s.status == "pending"]
    if len(pending) < 2:
        raise ConflictError("not enough pending stops to recalculate")

    delivery_map: dict[uuid.UUID, Delivery] = {}
    for s in pending:
        d = db.scalar(
            select(Delivery).where(Delivery.id == s.delivery_id, Delivery.organization_id == org_id)
        )
        if d:
            delivery_map[s.delivery_id] = d

    coords: list[tuple[float, float]] = []
    for s in pending:
        d = delivery_map.get(s.delivery_id)
        if d and d.dropoff_lat is not None and d.dropoff_lng is not None:
            coords.append((d.dropoff_lat, d.dropoff_lng))
        else:
            coords.append((0.0, 0.0))

    order = _nearest_neighbor_order(None, coords)
    base_seq = min(s.sequence for s in pending)
    for offset, idx in enumerate(order):
        pending[idx].sequence = base_seq + offset

    after = {
        "stops": [
            {"id": str(s.id), "delivery_id": str(s.delivery_id), "sequence": s.sequence}
            for s in route.stops
        ]
    }

    db.add(
        RouteRecalculation(
            organization_id=org_id,
            route_id=route.id,
            reason=reason,
            before_json=before,
            after_json=after,
        )
    )
    uow.flush()
    db.refresh(route)
    _recalc_totals(db, route)
    record(db, organization_id=org_id, actor_id=actor_id,
           action="route.recalculated", resource="route", resource_id=str(route.id))
    uow.commit()
    db.refresh(route)
    return route


def list_recalculations(
    uow: UnitOfWork, org_id: uuid.UUID, route_id: uuid.UUID
) -> list[RouteRecalculation]:
    get_route(uow, org_id, route_id)
    return list(
        uow.session.scalars(
            select(RouteRecalculation)
            .where(
                RouteRecalculation.organization_id == org_id,
                RouteRecalculation.route_id == route_id,
            )
            .order_by(RouteRecalculation.created_at.desc())
        )
    )