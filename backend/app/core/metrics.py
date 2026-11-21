from prometheus_client import Counter, Histogram

review_requests = Counter("prism_review_requests_total", "Review requests accepted")
review_failures = Counter("prism_review_failures_total", "Review processing failures")
review_duration = Histogram("prism_review_duration_seconds", "Review processing duration")
