import tempfile
from flask import Blueprint, jsonify, request
import ezdxf

from auth import require_user, resolve_identity
from supabase_rest import rest

bp = Blueprint("geometry", __name__)

def polygon_area(points):
    if len(points) < 3:
        return 0.0
    total = 0.0
    for i, a in enumerate(points):
        b = points[(i + 1) % len(points)]
        total += float(a[0]) * float(b[1]) - float(b[0]) * float(a[1])
    return abs(total) / 2.0

DXF_UNIT_TO_METRES = {
    1: 0.0254, 2: 0.3048, 3: 1609.344, 4: 0.001, 5: 0.01, 6: 1.0,
    7: 1000.0, 8: 0.0000254, 9: 0.000001, 10: 0.9144,
    13: 0.000001, 14: 0.1, 15: 10.0, 16: 100.0,
}

@bp.post("/api/geometry/calculate")
def calculate_geometry():
    payload = request.get_json(silent=True) or {}
    points = payload.get("points") or []
    if len(points) < 3:
        return jsonify({"error": "at_least_three_points_required"}), 400
    try:
        area = polygon_area(points)
    except Exception:
        return jsonify({"error": "invalid_points"}), 400
    return jsonify({
        "format": "LAYO-GEO-1.0",
        "area": area,
        "unit_squared": (payload.get("unit") or "m") + "²",
        "method": "polygon_shoelace",
    })

@bp.post("/api/geometry/dxf")
@require_user
def analyze_dxf():
    upload = request.files.get("file")
    if not upload:
        return jsonify({"error": "file_required"}), 400

    name = (upload.filename or "").lower()
    if name.endswith(".dwg"):
        return jsonify({
            "error": "dwg_conversion_required",
            "message": "DWG requires an approved DWG-to-DXF converter. Export DXF for immediate calculation.",
        }), 422
    if not name.endswith(".dxf"):
        return jsonify({"error": "dxf_required"}), 400

    with tempfile.NamedTemporaryFile(suffix=".dxf") as tmp:
        upload.save(tmp.name)
        try:
            doc = ezdxf.readfile(tmp.name)
        except Exception as exc:
            return jsonify({"error": "invalid_dxf", "detail": exc.__class__.__name__}), 422

        unit_code = int(doc.header.get("$INSUNITS", 0) or 0)
        factor = DXF_UNIT_TO_METRES.get(unit_code)
        candidates = []

        for entity in doc.modelspace():
            points = []
            try:
                if entity.dxftype() == "LWPOLYLINE":
                    points = [[float(x), float(y)] for x, y, *_ in entity.get_points()]
                    closed = bool(entity.closed)
                elif entity.dxftype() == "POLYLINE" and entity.is_2d_polyline:
                    points = [[float(v.dxf.location.x), float(v.dxf.location.y)] for v in entity.vertices]
                    closed = bool(entity.is_closed)
                else:
                    continue
                if len(points) >= 3:
                    candidates.append({
                        "points": points,
                        "closed": closed,
                        "area_raw": polygon_area(points),
                    })
            except Exception:
                continue

        if not candidates:
            return jsonify({"error": "no_polygon_polyline_found"}), 422

        candidates.sort(key=lambda x: x["area_raw"], reverse=True)
        polygon = candidates[0]
        return jsonify({
            "format": "LAYO-GEO-1.0",
            "source_type": "dxf",
            "insunits": unit_code,
            "unit_factor_to_metres": factor,
            "polylines_found": len(candidates),
            "closed": polygon["closed"],
            "points": polygon["points"],
            "area_raw": polygon["area_raw"],
            "area_m2": polygon["area_raw"] * (factor ** 2) if factor else None,
            "confidence": "cad-derived" if factor else "needs-unit-confirmation",
        })

@bp.post("/api/briefs/<brief_id>/geometry")
@require_user
def save_geometry(brief_id):
    identity = resolve_identity()
    payload = request.get_json(silent=True) or {}
    if not payload.get("area_m2"):
        return jsonify({"error": "area_required"}), 400

    body = {
        "brief_id": brief_id,
        "owner_user_id": identity["user_id"],
        "source_type": payload.get("source_type") or "unknown",
        "source_filename": payload.get("source_filename"),
        "unit": payload.get("unit") or "m",
        "geometry_json": {
            "format": payload.get("format", "LAYO-GEO-1.0"),
            "vertices": payload.get("vertices") or payload.get("points") or [],
            "normalized_vertices": payload.get("normalized_vertices") or [],
        },
        "source_metadata": payload.get("source_metadata") or {},
        "area_m2": payload.get("area_m2"),
        "area_method": payload.get("area_method"),
        "confidence": payload.get("confidence") or "unverified",
        "user_confirmed": bool(payload.get("user_confirmed")),
        "confirmed_at": payload.get("confirmed_at"),
    }
    rows = rest(
        "POST",
        "layo_geometry_models",
        identity["token"],
        json_body=body,
        prefer="return=representation",
    ) or []
    return jsonify(rows[0]), 201
