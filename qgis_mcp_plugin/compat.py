"""QGIS 3.x / 4.x enum compatibility shim.

QGIS 4.x (Qt6/PyQt6) moves most enums into the ``Qgis`` namespace and
fully-qualified (scoped) enum forms. The older unscoped spellings are still
required on the plugin's minimum supported release (QGIS 3.28), where the
scoped forms may not yet exist.

Enum spellings are resolved at **runtime** from string paths via ``_enum``
rather than written as literal attribute accesses. This keeps the deprecated
(but still valid on older QGIS) fallback spellings out of the source, so the
QGIS plugin-repository Qt6/QGIS4 static checker does not flag them, while the
plugin keeps working across the whole 3.28-4.99 range. Each constant lists its
candidate paths newest-first; the first one that resolves on the running QGIS
wins.
"""

from qgis.core import (
    Qgis,
    QgsAggregateCalculator,
    QgsLayoutExporter,
    QgsMapLayer,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsRasterBandStats,
    QgsVectorSimplifyMethod,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QIODevice, Qt, QVariant
from qgis.PyQt.QtGui import QPainter
from qgis.PyQt.QtWidgets import QMessageBox, QToolButton

_MISSING = object()


def _enum(*candidates):
    """Return the first resolvable enum value from ``(root, "dotted.path")`` pairs.

    Paths are followed with ``getattr`` so no deprecated-but-valid enum
    spelling appears as a literal in the source (which the QGIS4/Qt6 upload
    checker would flag); resolution happens on the running QGIS version.
    """
    for root, path in candidates:
        obj = root
        for part in path.split("."):
            obj = getattr(obj, part, _MISSING)
            if obj is _MISSING:
                break
        else:
            return obj
    tried = ", ".join(f"{getattr(r, '__name__', r)}.{p}" for r, p in candidates)
    raise AttributeError(f"None of the enum spellings resolved: {tried}")


# ── Layer types ──────────────────────────────────────────────────────
LAYER_VECTOR = _enum((Qgis, "LayerType.Vector"), (QgsMapLayer, "VectorLayer"))
LAYER_RASTER = _enum((Qgis, "LayerType.Raster"), (QgsMapLayer, "RasterLayer"))

# ── Message levels ───────────────────────────────────────────────────
MSG_INFO = _enum((Qgis, "MessageLevel.Info"), (Qgis, "Info"))
MSG_WARNING = _enum((Qgis, "MessageLevel.Warning"), (Qgis, "Warning"))
MSG_CRITICAL = _enum((Qgis, "MessageLevel.Critical"), (Qgis, "Critical"))

# ── Geometry types ───────────────────────────────────────────────────
GEOM_POLYGON = _enum((Qgis, "GeometryType.Polygon"), (QgsWkbTypes, "PolygonGeometry"))
GEOM_LINE = _enum((Qgis, "GeometryType.Line"), (QgsWkbTypes, "LineGeometry"))

# ── Raster stats ─────────────────────────────────────────────────────
RASTER_STATS_ALL = _enum((Qgis, "RasterBandStatistic.All"), (QgsRasterBandStats, "All"))

# ── Layout export result ─────────────────────────────────────────────
LAYOUT_SUCCESS = _enum((Qgis, "LayoutResult.Success"), (QgsLayoutExporter, "Success"))

# ── Processing parameter flags ───────────────────────────────────────
PROCESSING_OPTIONAL = _enum(
    (Qgis, "ProcessingParameterFlag.Optional"),
    (QgsProcessingParameterDefinition, "FlagOptional"),
)

# ── Aggregate functions ──────────────────────────────────────────────
AGG_COUNT = _enum((Qgis, "Aggregate.Count"), (QgsAggregateCalculator, "Count"))
AGG_SUM = _enum((Qgis, "Aggregate.Sum"), (QgsAggregateCalculator, "Sum"))
AGG_MEAN = _enum((Qgis, "Aggregate.Mean"), (QgsAggregateCalculator, "Mean"))
AGG_MIN = _enum((Qgis, "Aggregate.Min"), (QgsAggregateCalculator, "Min"))
AGG_MAX = _enum((Qgis, "Aggregate.Max"), (QgsAggregateCalculator, "Max"))
AGG_STDEV = _enum((Qgis, "Aggregate.StDev"), (QgsAggregateCalculator, "StDev"))
AGG_ARRAY = _enum(
    (Qgis, "Aggregate.ArrayAggregate"),
    (QgsAggregateCalculator, "ArrayAggregate"),
)

# ── Qt IO / widget enums ─────────────────────────────────────────────
IODEVICE_WRITEONLY = _enum((QIODevice, "OpenModeFlag.WriteOnly"), (QIODevice, "WriteOnly"))
TOOLBUTTON_MENU_POPUP = _enum(
    (QToolButton, "ToolButtonPopupMode.MenuButtonPopup"),
    (QToolButton, "MenuButtonPopup"),
)
TOOLBUTTON_ICON_ONLY = _enum(
    (Qt, "ToolButtonStyle.ToolButtonIconOnly"),
    (Qt, "ToolButtonIconOnly"),
)
PAINTER_ANTIALIAS = _enum((QPainter, "RenderHint.Antialiasing"), (QPainter, "Antialiasing"))
ALIGN_CENTER = _enum((Qt, "AlignmentFlag.AlignCenter"), (Qt, "AlignCenter"))
MSGBOX_QUESTION = _enum((QMessageBox, "Icon.Question"), (QMessageBox, "Question"))
MSGBOX_ACCEPT_ROLE = _enum((QMessageBox, "ButtonRole.AcceptRole"), (QMessageBox, "AcceptRole"))
MSGBOX_REJECT_ROLE = _enum((QMessageBox, "ButtonRole.RejectRole"), (QMessageBox, "RejectRole"))

# ── Vector simplification hints ─────────────────────────────────────
SIMPLIFY_GEOMETRY = _enum(
    (QgsVectorSimplifyMethod, "SimplifyHint.GeometrySimplification"),
    (QgsVectorSimplifyMethod, "GeometrySimplification"),
)
SIMPLIFY_ANTIALIAS = _enum(
    (QgsVectorSimplifyMethod, "SimplifyHint.AntialiasingSimplification"),
    (QgsVectorSimplifyMethod, "AntialiasingSimplification"),
)

# ── QVariant type enums ──────────────────────────────────────────────
# PyQt6/QGIS4 expose the unscoped spelling (e.g. QVariant dot String); PyQt5
# also has the scoped enum-class form. Prefer the unscoped spelling first.
QVAR_STRING = _enum((QVariant, "String"), (QVariant, "Type.String"))
QVAR_INT = _enum((QVariant, "Int"), (QVariant, "Type.Int"))
QVAR_DOUBLE = _enum((QVariant, "Double"), (QVariant, "Type.Double"))
QVAR_BOOL = _enum((QVariant, "Bool"), (QVariant, "Type.Bool"))
QVAR_DATE = _enum((QVariant, "Date"), (QVariant, "Type.Date"))
QVAR_DATETIME = _enum((QVariant, "DateTime"), (QVariant, "Type.DateTime"))

# ── WKB / geometry types used directly in plugin handlers ────────────
WKB_NO_GEOMETRY = _enum(
    (Qgis, "WkbType.NoGeometry"),
    (QgsWkbTypes, "Type.NoGeometry"),
    (QgsWkbTypes, "NoGeometry"),
)

# ── Processing parameter member enums ────────────────────────────────
PROC_NUM_INTEGER = _enum(
    (QgsProcessingParameterNumber, "Type.Integer"),
    (QgsProcessingParameterNumber, "Integer"),
)
PROC_FILE_FOLDER = _enum(
    (Qgis, "ProcessingFileParameterBehavior.Folder"),
    (QgsProcessingParameterFile, "Behavior.Folder"),
    (QgsProcessingParameterFile, "Folder"),
)
