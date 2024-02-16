from collections import OrderedDict

import structlog

def configure_structlog():
    """Configure the default behaviour of the structlog logging package."""
    global configured
    structlog.configure_once(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            # structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=structlog.threadlocal.wrap_dict(OrderedDict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    configured = True


def get_logger(name, local=False, **context) -> structlog.stdlib.BoundLogger:
    """Creates a logger instance, detached from thread-local scope if local=True, with the given
    context inserted
    """
    global configured
    if not configured:
        configure_structlog()

    logger = structlog.get_logger(name)

    if local:
        logger = structlog.threadlocal.as_immutable(logger)

    if context:
        logger = logger.bind(**context)
    else:
        logger = logger.bind()

    return logger