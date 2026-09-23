import base64
import tempfile

import cv2
import ezdxf
import fitz
import numpy as np
from flask import Blueprint, jsonify, request

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

def _image_from_upload(upload):
    raw = upload.read()
    name = (upload.filename or "").lower()

    if name.endswith(".pdf") or upload.mimetype == "application/pdf":
        doc = fitz.open(stream=raw, filetype="pdf")
        if doc.page_count < 1:
            raise ValueError("empty_pdf")
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image, "pdf-first-page"

    arr = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("unsupported_image")
    return image, "image"

def _auto_boundary(image):
    height, width = image.shape[:2]
    max_width = 1400
    if width > max_width:
        scale = max_width / width
        image = cv2.resize(
            image,
            (max_width, max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
        height, width = image.shape[:2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        np.ones((5, 5), np.uint8),
        iterations=2,
    )
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    image_area = float(width * height)
    candidates = []
    for contour in contours:
        area = abs(cv2.contourArea(contour))
        if area < image_area * 0.01 or area > image_area * 0.97:
            continue
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, max(2.0, 0.012 * perimeter), True)
        points = [[float(p[0][0]), float(p[0][1])] for p in polygon]
        if 3 <= len(points) <= 80:
            candidates.append((area, points))

    if not candidates:
        raise ValueError("boundary_not_found")

    candidates.sort(key=lambda x: x[0], reverse=True)
    points = candidates[0][1]
    ok, encoded = cv2.imencode(".png", image)
    preview = (
        "data:image/png;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")
        if ok else None
    )
    return points, width, height, preview

@bp.post("/api/geometry/image")
@require_user
def analyze_image_or_pdf():
    upload = request.files.get("file")
    if not upload:
        return jsonify({"error": "file_required"}), 400

    try:
        image, source_kind = _image_from_upload(upload)
        points, width, height, preview = _auto_boundary(image)
    except ValueError as exc:
        return jsonify({
            "error": str(exc),
            "message": "No reliable automatic outer boundary was found. Trace the boundary manually or upload a cleaner plan.",
        }), 422

    return jsonify({
        "format": "LAYO-GEO-1.0",
        "source_type": source_kind,
        "method": "opencv-largest-outer-contour",
        "confidence": "auto-trace-draft",
        "points": points,
        "image_width": width,
        "image_height": height,
        "preview_data_url": preview,
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
