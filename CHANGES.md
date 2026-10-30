# Changelog

## [1.4.1](https://github.com/ZeitOnline/opentelemetry-prometheus-multiprocess/compare/1.4.0...1.4.1) (2026-10-30)


### Maintenance

* release with Release Please via the shared pypi-release workflow ([#4](https://github.com/ZeitOnline/opentelemetry-prometheus-multiprocess/issues/4)) ([25b341f](https://github.com/ZeitOnline/opentelemetry-prometheus-multiprocess/commit/25b341fa39f39f3e8c5ca57a5f156d91612c7661))

## 1.4.0 (2026-04-17)

- Prevent unbounded growth of label consistency check state (labels)

## 1.3.0 (2026-04-13)

- Ignore otel sdk internal metrics, they use async/observable collection, which we do not support (otel)

## 1.2.3 (2025-02-06)

- More updates to otel 1.30 API (otel)

## 1.2.2 (2025-02-05)

- More updates to otel 1.30 API (otel)

## 1.2.1 (2025-02-05)

- Update to otel 1.30 API (otel)

## 1.2.0 (2024-12-20)

- Support seconds as well as milliseconds in histogram buckets (histogram)

## 1.1.2 (2024-11-07)

- otel: Update to otel 1.28 API (otel)

## 1.1.1 (2024-11-07)

- Accept kw to make otel API forward-compatible (fwcompat)

## 1.1.0 (2024-06-25)

- naming: Conform to prometheus metric name and unit conventions (naming)

## 1.0.0 (2024-04-26)

- Initial release (initial)
