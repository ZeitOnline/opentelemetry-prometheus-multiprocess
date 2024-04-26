================================================================
OpenTelemetry Prometheus MeterProvider with multiprocess support
================================================================

Workaround to use `prometheus_client multiprocess mode <https://github.com/prometheus/client_python/#multiprocess-mode-eg-gunicorn>`_ (for e.g. gunicorn, celery) with opentelemetry,
where this model currently is `not supported <https://github.com/open-telemetry/opentelemetry-python/issues/93>`_,
and not even employing an additional otel collector `currently solves this <https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/4968>`_.

This package provides a customized ``MeterProvider``,
that uses the native ``prometheus_client`` metrics implementations,
and thus their mechanisms for exporting/exposition (and not the opentelemetry ones).

Usage
=====

* See `Multiprocess Mode Documentation <https://prometheus.github.io/client_python/multiprocess/>`_ for details on how to operate this.

* Set environment variable ``PROMETHEUS_MULTIPROC_DIR`` to a directory
  where ``prometheus_client`` can store its metrics state files
  (that are shared between processes via mmap).

* Configure opentelemetry meter provider::

   from opentelemetry.sdk.extension.prometheus_multiprocess import PrometheusMeterProvider
   import opentelemetry.metrics

   provider = PrometheusMeterProvider()
   opentelemetry.metrics.set_meter_provider(provider)

* Set up prometheus metrics exposition, for example::

    registry = prometheus_client.CollectorRegistry()
    prometheus_client.multiprocess.MultiProcessCollector(registry)
    prometheus_client.start_http_server(8080, registry=registry)

  (The package also provides a ``MultiProcessRegistry`` to streamline this setup.)

* Use opentelemetry metrics like normal::

    meter = opentelemetry.metrics.get_meter('mypackage', 'myversion')
    HTTP_DURATION = metrics.create_histogram('http.client.duration', unit='ms')

    from timeit import default_timer
    start = default_timer()
    # perform request here
    duration = (default_timer() - start) * 1000
    HTTP_DURATION.record(duration, {'http.response.status_code': 200})
