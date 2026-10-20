"""Shared OpenTelemetry setup, used by every collector."""
import os

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


def setup_metrics(service_name: str):
    """Start pushing metrics to the OTel Collector. Returns the provider, or None if disabled.

    Metrics are only enabled when OTEL_EXPORTER_OTLP_ENDPOINT is set, so running
    a collector on your own machine without a cluster still works.
    """
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return None
    reader = PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=60_000)
    provider = MeterProvider(
        resource=Resource.create({"service.name": service_name}),  # labels the data by collector
        metric_readers=[reader],
    )
    metrics.set_meter_provider(provider)
    return provider