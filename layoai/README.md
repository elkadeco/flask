# LayoAI live integration v2.1 — Geometry Intelligence + Auto Trace

This branch is connected to the existing LayoAI Supabase project at the application-contract level.

## Live foundation completed
- Supabase project restored.
- Customer portal tables created with Row Level Security.
- Private `layoai-private` Storage bucket created with per-user folder policies.
- Email OTP-compatible authentication boundary.
- Customer brief cloud save/resume endpoints.
- Rooms and file metadata contracts.
- Server-side OpenAI Agents SDK intake endpoint with persistent session adapter.
- 15-language locale registry with English fallback and RTL metadata.
- Designer access remains allowlist-protected.
- Health endpoint truthfully reports readiness.

## Site Geometry Intelligence
The file stage supports a governed geometry workflow:

1. **UTM coordinates** — redraw a polygon from Easting/Northing points and calculate area mathematically.
2. **Known dimensions** — calculate and redraw a rectangular site from supplied length × width.
3. **CAD / DXF-DWG** — DXF closed polylines can be extracted and area-calculated. DWG requires an approved conversion adapter or DXF export.
4. **Sketch / photo / PDF** — authenticated users can request automatic outer-boundary tracing. The backend renders the first PDF page when needed and uses OpenCV to return a draft polygon. The client can correct the trace, calibrate one known edge and confirm the result.

Confirmed geometry is stored as **LAYO-GEO-1.0** with source type, vertices, normalized geometry, area, calculation method, confidence and explicit client confirmation.

The system distinguishes:
- mathematical precision of the calculation;
- accuracy/quality of the source geometry;
- client confirmation;
- legal/survey verification.

A perspective photograph remains an estimate even after calibration. A UTM/survey/CAD polygon can support a much stronger area result, subject to the correctness of the supplied source.

## Still needs deployment environment configuration
- Finish secure OpenAI API key setup and set `OPENAI_API_KEY` on the hosting service.
- Set `OPENAI_MODEL` after model/task evaluation.
- Add the approved designer email(s) to `DESIGNER_EMAIL_ALLOWLIST`.
- Copy the current v2.1 visual shell to `layoai/frontend/index.html` in the deployment bundle.
- Add an approved DWG conversion service if direct DWG ingestion is required.

SMS/WhatsApp verification is not enabled. No fake success state is used.
