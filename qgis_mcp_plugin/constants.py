"""Values shared by the server, the plugin entry point and the configurator.

Stdlib-only and free of ``qgis`` imports, like :mod:`wire`, :mod:`errors` and
:mod:`registry`. Keeping them here is what lets ``configurator`` read the
settings prefix without importing ``plugin``, which imports it back.
"""

import errno
import os

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876

# The plugin package directory — where metadata.txt and icons/ live. Anchored
# here rather than on each module's own ``__file__`` so a module inside a
# subpackage (``handlers/``) still resolves them correctly.
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

# QgsSettings key prefix for every setting the plugin persists.
SETTINGS_PREFIX = "qgis_mcp"

# "someone else already holds this port". EADDRINUSE is the usual answer, and is
# what a second QGIS window gets since both sides set SO_EXCLUSIVEADDRUSE. Windows
# answers WSAEACCES instead when the other holder used plain SO_REUSEADDR, which
# means the same thing here — the spin box floor is 1024, so EACCES cannot be the
# "privileged port" case.
ADDR_IN_USE = frozenset({errno.EADDRINUSE, errno.EACCES, 10048, 10013})
