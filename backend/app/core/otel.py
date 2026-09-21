import structlog
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings

log = structlog.get_logger("otel")


def setup_tracing() -> None:
    if settings.ENV == "prod":
        # Replace with OTLP exporter to your collector in prod
        return
    resource = Resource.create({"service.name": settings.APP_NAME, "env": settings.ENV})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    log.info("otel_configured", env=settings.ENV)