from threading import Lock
from typing import Dict, Optional, Sequence, Union
import logging
import re

from opentelemetry.metrics import (
    MeterProvider,
    Meter,
    NoOpMeter,
    Instrument,
    CallbackT,
    Counter,
    _Gauge as Gauge,
    Histogram,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.sdk.util.instrumentation import InstrumentationScope
from prometheus_client.samples import Sample
import prometheus_client
import prometheus_client.metrics


_logger = logging.getLogger(__name__)


class PrometheusMeterProvider(MeterProvider):

    def __init__(self) -> None:
        self._meter_lock = Lock()
        self._meters = {}

    # Taken from opentelemetry.sdk.metrics.MeterProvider
    def get_meter(
        self,
        name: str,
        version: Optional[str] = None,
        schema_url: Optional[str] = None,
    ) -> Meter:
        if not name:
            _logger.warning('Meter name cannot be None or empty.')
            return NoOpMeter(name, version=version, schema_url=schema_url)

        info = InstrumentationScope(name, version, schema_url)
        with self._meter_lock:
            if not self._meters.get(info):
                self._meters[info] = PrometheusMeter(info)
            return self._meters[info]


class PrometheusMeter(Meter):

    def __init__(self, instrumentation_scope: InstrumentationScope) -> None:
        super().__init__(
            instrumentation_scope.name,
            instrumentation_scope.version,
            instrumentation_scope.schema_url)
        self._instrument_id_instrument = {}
        self._instrument_id_instrument_lock = Lock()

    # Extracted from opentelemetry.sdk.metrics.Meter
    def _create(self, api, cls, name, unit, description) -> Instrument:
        (
            is_instrument_registered,
            instrument_id,
        ) = self._is_instrument_registered(name, cls, unit, description)

        if is_instrument_registered:
            _logger.warning(
                'An instrument with name %s, type %s, unit %s and '
                'description %s has been created already.',
                name,
                api.__name__,
                unit,
                description,
            )
            with self._instrument_id_instrument_lock:
                return self._instrument_id_instrument[instrument_id]

        instrument = cls(name, unit, description)
        with self._instrument_id_instrument_lock:
            self._instrument_id_instrument[instrument_id] = instrument
            return instrument

    def create_counter(
        self,
        name: str,
        unit: str = '',
        description: str = '',
    ) -> Counter:
        return self._create(
            Counter, PrometheusCounter, name, unit, description)

    def create_up_down_counter(
        self,
        name: str,
        unit: str = '',
        description: str = '',
    ) -> UpDownCounter:
        return self._create(
            UpDownCounter, PrometheusUpDownCounter, name, unit, description)

    def create_gauge(
        self,
        name: str,
        unit: str = '',
        description: str = '',
    ) -> Gauge:
        return self._create(Gauge, PrometheusGauge, name, unit, description)

    def create_histogram(
        self,
        name: str,
        unit: str = '',
        description: str = '',
    ) -> Histogram:
        return self._create(
            Histogram, PrometheusHistogram, name, unit, description)

    def create_observable_counter(
        self,
        name: str,
        callbacks: Optional[Sequence[CallbackT]] = None,
        unit: str = '',
        description: str = '',
    ) -> ObservableCounter:
        raise NotImplementedError(
            'Observable/Asynchronous instruments not supported for Prometheus')

    def create_observable_up_down_counter(
        self,
        name: str,
        callbacks: Optional[Sequence[CallbackT]] = None,
        unit: str = '',
        description: str = '',
    ) -> ObservableUpDownCounter:
        raise NotImplementedError(
            'Observable/Asynchronous instruments not supported for Prometheus')

    def create_observable_gauge(
        self,
        name: str,
        callbacks: Optional[Sequence[CallbackT]] = None,
        unit: str = '',
        description: str = '',
    ) -> ObservableGauge:
        raise NotImplementedError(
            'Observable/Asynchronous instruments not supported for Prometheus')


class PrometheusMetric:

    metric_cls: type[prometheus_client.metrics.MetricWrapperBase] = object
    metric_kw = {}

    def __init__(
            self,
            name: str,
            unit: str = '',
            description: str = '',
    ) -> None:
        super().__init__(name, unit=unit, description=description)
        self._metric = self.metric_cls(
            self._sanitize(name), description, unit=unit, **self.metric_kw)

    NON_ALPHANUMERIC = re.compile(r'[^\w]')

    def _sanitize(self, text: str) -> str:
        # Taken from opentelemetry-exporter-prometheus
        return self.NON_ALPHANUMERIC.sub('_', text)

    def metric(
            self, attributes: Dict[str, str] = None
    ) -> prometheus_client.metrics.MetricWrapperBase:
        return self._metric


def _multi_samples_with_labels(self):
    with self._lock:
        metrics = self._metrics.copy()
    for labels, metric in metrics.items():
        series_labels = list(zip(self._labelnames, labels))
        for suffix, sample_labels, value, timestamp, exemplar in metric._samples():
            yield Sample(
                suffix, dict(series_labels + list(sample_labels.items())),
                value, timestamp, exemplar)


class PrometheusCounter(PrometheusMetric, Counter):

    metric_cls = prometheus_client.Counter

    def add(
        self, amount: Union[int, float], attributes: Dict[str, str] = None
    ):
        if amount < 0:
            _logger.warning(
                'Add amount must be non-negative on Counter %s.', self.name
            )
            return
        self.metric(attributes).inc(amount)


class PrometheusUpDownCounter(PrometheusMetric, UpDownCounter):

    metric_cls = prometheus_client.Gauge

    def add(
        self, amount: Union[int, float], attributes: Dict[str, str] = None
    ):
        self.metric(attributes).inc(amount)


class PrometheusGauge(PrometheusMetric, Gauge):

    metric_cls = prometheus_client.Gauge

    def set(
        self, amount: Union[int, float], attributes: Dict[str, str] = None
    ):
        self.metric(attributes).set(amount)


class PrometheusHistogram(PrometheusMetric, Histogram):

    metric_cls = prometheus_client.Histogram
    metric_kw = {'buckets': (
        # Taken from opentelemetry.sdk.aggregation
        0.0,
        5.0,
        10.0,
        25.0,
        50.0,
        75.0,
        100.0,
        250.0,
        500.0,
        750.0,
        1000.0,
        2500.0,
        5000.0,
        7500.0,
        10000.0,
    )}

    def record(
        self, amount: Union[int, float], attributes: Dict[str, str] = None
    ):
        if amount < 0:
            _logger.warning(
                'Record amount must be non-negative on Histogram %s.', self.name
            )
            return
        self.metric(attributes).observe(amount)
