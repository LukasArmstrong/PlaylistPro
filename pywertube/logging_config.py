import os
import logging
import structlog

# Global logger variable
gLogger = None


def initLogger(file, debug=False, verbose=False):
    """Initialize and configure structlog for the application."""
    global gLogger

    # Standard Python logging levels: debug > Info > warning > error > critical
    if debug:
        if verbose:
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.stdlib.add_log_level,
                    structlog.processors.CallsiteParameterAdder(
                        [structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                        structlog.processors.CallsiteParameter.PROCESS,
                        structlog.processors.CallsiteParameter.THREAD]
                    ),
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.dict_tracebacks,
                    structlog.dev.ConsoleRenderer(),
                ],
                wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
                context_class=dict,
                cache_logger_on_first_use=True
            )
        else:
            structlog.configure(
                processors=[
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.stdlib.add_log_level,
                    structlog.processors.CallsiteParameterAdder(
                        [structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                        structlog.processors.CallsiteParameter.PROCESS,
                        structlog.processors.CallsiteParameter.THREAD]
                    ),
                    structlog.processors.dict_tracebacks,
                    structlog.dev.ConsoleRenderer(),
                ],
                wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
                context_class=dict,
                cache_logger_on_first_use=True
            )
    else:
        BASE_DIR = os.path.dirname(file)
        os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
        LOG_FILE = f"{BASE_DIR}/logs/{os.path.basename(file)[:-3]}.log"

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_log_level,
                structlog.processors.EventRenamer("msg"),
                structlog.processors.CallsiteParameterAdder(
                    [structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.PROCESS,
                    structlog.processors.CallsiteParameter.THREAD]
                ),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(
                file=open(LOG_FILE,'a+')
            ),
            cache_logger_on_first_use=True
        )

    gLogger = structlog.get_logger()
    gLogger.debug("Logger Created!")
    return gLogger


def setLogger(logger):
    """Set the global logger instance."""
    global gLogger
    logger.debug("Enter...")
    gLogger = logger
    gLogger.debug("Logger set!")
    gLogger.debug("Leaving...")


def getLogger():
    """Get the current global logger instance."""
    global gLogger
    return gLogger
