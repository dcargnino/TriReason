"""Entry point: python -m trireason"""

import uvicorn

from trireason.config import settings

uvicorn.run(
    "trireason.app:app",
    host=settings.app_host,
    port=settings.app_port,
    log_level=settings.log_level,
    reload=True,
)
