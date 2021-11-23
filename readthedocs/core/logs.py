import structlog

from django_structlog.middlewares.request import RequestMiddleware


class ReadTheDocsRequestMiddleware(RequestMiddleware):

    """
    ``ReadTheDocsRequestMiddleware`` adds request metadata to ``structlog``'s logger context.

    This middleware overrides the original ``format_request`` to log the full
    URL instead of just its path.

    >>> MIDDLEWARE = [
    ...     # ...
    ...     'readthedocs.core.logs.ReadTheDocsRequestMiddleware',
    ... ]

    """

    def format_request(self, request):
        return request.build_absolute_uri()


class NewRelicProcessor:

    """
    New Relic structlog's processor.

    It adds extra fields. Borrowed from
    https://github.com/newrelic/newrelic-python-agent/blob/c1764f8a/newrelic/api/log.py#L39

    It must be *before*
    ``structlog.stdlib.ProcessorFormatter.remove_processors_meta`` to have
    access to ``_record`` key.
    """

    def __call__(self, logger, method_name, event_dict):
        # Import ``newrelic`` here because it's only installed in production
        from newrelic.api.log import format_exc_info  # noqa
        from newrelic.api.time_trace import get_linking_metadata  # noqa

        if not isinstance(event_dict, dict):
            return event_dict

        record = event_dict.get('_record')
        if record is None:
            return event_dict

        event_dict.update(get_linking_metadata())

        output = {
            # "timestamp": int(record.created * 1000),
            # "message": record.getMessage(),
            "message": event_dict['event'],
            # "log.level": record.levelname,
            # "logger.name": record.name,
            "thread.id": record.thread,
            "thread.name": record.threadName,
            "process.id": record.process,
            "process.name": record.processName,
            "file.name": record.pathname,
            "line.number": record.lineno,
        }

        if record.exc_info:
            output.update(format_exc_info(record.exc_info))

        event_dict.update(output)
        return event_dict


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        # Remove `format_exc_info` from your processor chain if you want pretty exceptions.
        # structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
