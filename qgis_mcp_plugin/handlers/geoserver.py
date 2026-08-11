"""GeoServer publication artifact export."""

import os
import re
from pathlib import Path

try:
    from datetime import UTC, datetime
except ImportError:  # Python 3.9 used by older supported QGIS releases
    from datetime import datetime, timezone

    UTC = timezone.utc  # noqa: UP017

from qgis.core import QgsDataSourceUri, QgsProject, QgsWkbTypes

from ..compat import LAYER_VECTOR
from ..errors import CommandError
from ..registry import command


class GeoServerHandlers:
    """Export vector metadata and SLD files for GeoServer publishing."""

    @command
    def export_geoserver_publish_manifest(
        self,
        output_dir=None,
        include_hidden=True,
        include_invalid=False,
        overwrite=True,
        **kwargs,
    ):
        project = QgsProject.instance()
        configured_output_dir = output_dir or os.environ.get("QGIS_MCP_GEOSERVER_EXPORT_DIR")
        output_root = Path(configured_output_dir or Path.home() / ".qgis_mcp" / "geoserver_styles")
        try:
            output_root.mkdir(parents=True, exist_ok=True)
            resolved_output = output_root.resolve()
        except (OSError, RuntimeError) as ex:
            raise CommandError(f"Could not prepare GeoServer style output directory: {ex}") from ex

        manifest = {
            "ok": True,
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "project": {
                "title": project.title(),
                "filename": project.fileName(),
                "crs": project.crs().authid(),
            },
            "sld_output_dir": str(resolved_output),
            "summary": {
                "total_layers": len(project.mapLayers()),
                "vector_layers": 0,
                "exported_styles": 0,
                "failed_styles": 0,
                "skipped_non_vector": 0,
                "skipped_invalid": 0,
            },
            "layers": [],
            "errors": [],
        }

        for layer_id, layer in project.mapLayers().items():
            if layer.type() != LAYER_VECTOR:
                manifest["summary"]["skipped_non_vector"] += 1
                continue

            tree_layer = project.layerTreeRoot().findLayer(layer_id)
            visible = bool(tree_layer.isVisible()) if tree_layer is not None else True
            if not include_hidden and not visible:
                continue

            manifest["summary"]["vector_layers"] += 1
            valid = bool(layer.isValid())
            if not valid and not include_invalid:
                manifest["summary"]["skipped_invalid"] += 1
                continue

            layer_errors = []
            source_meta = self._geoserver_layer_source_metadata(layer)
            safe_name = self._safe_geoserver_name(layer.name())
            layer_name = source_meta.get("table") or safe_name
            style_name = safe_name
            sld_path = output_root / f"{safe_name}__{layer_id[:8]}.sld"
            style = {
                "format": "sld",
                "style_name": style_name,
                "path": str(sld_path.resolve()),
                "exported": False,
                "message": "",
            }
            if not overwrite and sld_path.exists():
                style["exported"] = True
                style["message"] = "Style already exists"
                manifest["summary"]["exported_styles"] += 1
            else:
                try:
                    message, success = layer.saveSldStyle(str(sld_path))
                    style["message"] = message
                    style["exported"] = bool(success)
                    if success:
                        manifest["summary"]["exported_styles"] += 1
                    else:
                        manifest["summary"]["failed_styles"] += 1
                        layer_errors.append(f"Failed to export SLD style: {message}")
                except Exception as ex:
                    manifest["summary"]["failed_styles"] += 1
                    style["message"] = str(ex)
                    layer_errors.append(f"Failed to export SLD style: {ex}")

            crs = layer.crs()
            epsg = crs.postgisSrid() if crs.isValid() else 0
            manifest["layers"].append(
                {
                    "id": layer.id(),
                    "name": layer.name(),
                    "visible": visible,
                    "valid": valid,
                    "provider": layer.providerType(),
                    "source": source_meta.get("source"),
                    "schema": source_meta.get("schema"),
                    "table": source_meta.get("table"),
                    "geometry_column": source_meta.get("geometry_column"),
                    "datasource": source_meta.get("datasource"),
                    "crs": {"authid": crs.authid(), "epsg": epsg if epsg > 0 else None},
                    "geometry": {
                        "geometry_type": layer.geometryType(),
                        "wkb_type": QgsWkbTypes.displayString(layer.wkbType()),
                    },
                    "fields": [
                        {
                            "name": field.name(),
                            "type": int(field.type()),
                            "type_name": field.typeName(),
                            "length": field.length(),
                            "precision": field.precision(),
                            "is_numeric": field.isNumeric(),
                        }
                        for field in layer.fields()
                    ],
                    "style": style,
                    "geoserver": {"layer_name": layer_name, "style_name": style_name},
                    "errors": layer_errors,
                }
            )

        return manifest

    @staticmethod
    def _safe_geoserver_name(value):
        slug = re.sub(r"[^0-9A-Za-z_]+", "_", str(value).strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")
        if not slug:
            slug = "layer"
        if slug[0].isdigit():
            slug = f"layer_{slug}"
        return slug

    @staticmethod
    def _sanitize_datasource(source):
        try:
            sanitized = str(QgsDataSourceUri.removePassword(source))
        except Exception:
            sanitized = str(source)
        return re.sub(
            r"(?i)(password|passwd|pwd)=('[^']*'|\"[^\"]*\"|[^\s&]+)",
            r"\1=<redacted>",
            sanitized,
        )

    def _geoserver_layer_source_metadata(self, layer):
        source = layer.source()
        sanitized = self._sanitize_datasource(source)
        metadata = {
            "source": sanitized,
            "schema": None,
            "table": None,
            "geometry_column": None,
            "datasource": {},
        }
        try:
            uri = QgsDataSourceUri(source)
            metadata["schema"] = str(uri.schema()) or None
            metadata["table"] = str(uri.table()) or None
            metadata["geometry_column"] = str(uri.geometryColumn()) or None
            metadata["datasource"] = {
                "database": str(uri.database()) or None,
                "host": str(uri.host()) or None,
                "port": str(uri.port()) or None,
                "service": str(uri.service()) or None,
                "authcfg": str(uri.authConfigId()) or None,
                "key_column": str(uri.keyColumn()) or None,
            }
        except Exception as ex:
            metadata["datasource"] = {"parse_error": str(ex)}

        if not metadata["table"]:
            metadata["schema"], metadata["table"], metadata["geometry_column"] = (
                self._parse_table_from_source(sanitized)
            )
        return metadata

    @staticmethod
    def _parse_table_from_source(source):
        match = re.search(
            r'table="?([^".\s]+)"?\."?([^"\s(]+)"?(?:\s*\(([^)]+)\))?',
            source,
            re.IGNORECASE,
        )
        if match:
            return match.group(1), match.group(2), match.group(3)
        match = re.search(r'table="?([^"\s(]+)"?(?:\s*\(([^)]+)\))?', source, re.IGNORECASE)
        if match:
            return None, match.group(1), match.group(2)
        return None, None, None
