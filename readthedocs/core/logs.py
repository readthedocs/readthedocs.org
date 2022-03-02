import sys
import warnings

from io import StringIO

import structlog
from structlog.dev import _pad, plain_traceback

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


class SysLogRenderer(structlog.dev.ConsoleRenderer):
    def __call__(self, logger, name, event_dict):
        sio = StringIO()

        # ``readthedocs`` as programname is required because it's used by
        # syslog to filter messages and send them to different files.
        # https://www.rsyslog.com/doc/master/configuration/properties.html#message-properties
        sio.write("readthedocs")

        process_id = event_dict.pop("process_id", None)
        if process_id is not None:
            sio.write(
                "["
                + str(process_id)
                + "]"
            )

        # syslog tag delimiter
        sio.write(": ")

        ts = event_dict.pop("timestamp", None)
        if ts is not None:
            sio.write(
                # can be a number if timestamp is UNIXy
                self._styles.timestamp
                + str(ts)
                + self._styles.reset
                + " "
            )

        level = event_dict.pop("level", None)
        if level is not None:
            sio.write(
                "["
                + self._level_to_color.get(level, "")
                + _pad(level, self._longest_level)
                + self._styles.reset
                + "] "
            )

        # force event to str for compatibility with standard library
        event = event_dict.pop("event", None)
        if not isinstance(event, str):
            event = str(event)

        if event_dict:
            event = _pad(event, self._pad_event) + self._styles.reset + " "
        else:
            event += self._styles.reset
        sio.write(self._styles.bright + event)

        logger_name = event_dict.pop("logger", None)
        if logger_name is None:
            logger_name = event_dict.pop("logger_name", None)

        line_number = event_dict.pop("line_number", None)
        if logger_name is not None:
            sio.write(
                "["
                + self._styles.logger_name
                + self._styles.bright
                + logger_name
                + self._styles.reset
                + ":"
                + str(line_number)
                + "] "
            )

        stack = event_dict.pop("stack", None)
        exc = event_dict.pop("exception", None)
        exc_info = event_dict.pop("exc_info", None)

        event_dict_keys = event_dict.keys()
        if self._sort_keys:
            event_dict_keys = sorted(event_dict_keys)

        sio.write(
            " ".join(
                self._styles.kv_key
                + key
                + self._styles.reset
                + "="
                + self._styles.kv_value
                + self._repr(event_dict[key])
                + self._styles.reset
                for key in event_dict_keys
            )
        )

        if stack is not None:
            sio.write("\n" + stack)
            if exc_info or exc is not None:
                sio.write("\n\n" + "=" * 79 + "\n")

        if exc_info:
            if not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()

            self._exception_formatter(sio, exc_info)
        elif exc is not None:
            if self._exception_formatter is not plain_traceback:
                warnings.warn(
                    "Remove `format_exc_info` from your processor chain "
                    "if you want pretty exceptions."
                )
            sio.write("\n" + exc)

        return sio.getvalue()


class SysLogProcessor:

    def __call__(self, logger, method_name, event_dict):
        record = event_dict.get('_record', None)
        if record is None:
            return event_dict

        event_dict.update({
            'process_id': record.process,
            'line_number': record.lineno,
        })
        return event_dict


shared_processors = [
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.UnicodeDecoder(),
]

structlog.configure(
    processors=list([
        structlog.stdlib.filter_by_level,
        *shared_processors,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]),
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
