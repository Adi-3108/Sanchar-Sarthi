# EventFlow AI API Specification

## 1. API Standards

Base URL:

```text
/api
```

MVP authentication uses Firebase Auth plus a three-level EventFlow access model.  
Rate limits: enforce simple IP-based or in-memory limits in MVP for report endpoints.

Access levels:

| Level | Name | MVP Auth | Scope |
|---|---|---|---|
| Level 1 | Admin / Control Room | Firebase Auth email/password + backend role check | officer management, dataset upload/load, demo reset, full command view |
| Level 2 | Registered Police Officer | Firebase Auth email/password + officer assignment check | assigned event plans, officer-safe routing/diversion overlays, field updates, report confirmation |
| Level 3 | Public / Citizen | no login, rate-limited | public advisories and citizen reports |

Protected endpoint auth contract:

```text
Header: Authorization: Bearer <firebase_id_token>
Missing token: 401 MISSING_FIREBASE_TOKEN
Invalid token: 401 INVALID_FIREBASE_TOKEN
Revoked token: 401 REVOKED_FIREBASE_TOKEN
Firebase Admin not configured: 503 FIREBASE_NOT_CONFIGURED
Inactive account: 403 INACTIVE_ACCOUNT
Wrong role: 403 FORBIDDEN_ROLE
Unassigned officer: 403 OFFICER_ASSIGNMENT_REQUIRED
```

Firebase login proves identity only. FastAPI must still verify the user's EventFlow role and officer/station/corridor assignment from PostgreSQL.

Common error response:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error",
    "details": {}
  }
}
```

## 2. GET /api/health

**Description:** Verify backend, database, and model availability.  
**Authentication:** none in demo.  
**Authorization:** Level 3 public-safe endpoint.

Response:

```json
{
  "status": "ok",
  "service": "eventflow-ai-backend",
  "database": "connected",
  "models": {
    "priority": "loaded",
    "road_closure": "loaded"
  }
}
```

## 3. POST /api/datasets/load-demo

**Description:** Load bundled cleaned/demo ASTraM data.  
**Authentication:** Level 1 Admin / Control Room Firebase user required.  
**Rate limit:** 3/hour.

Response:

```json
{
  "status": "success",
  "rows_loaded": 8173,
  "columns_detected": 46,
  "invalid_rows": 0,
  "message": "Demo dataset loaded."
}
```

Errors:

- DATASET_NOT_FOUND
- DATABASE_UNAVAILABLE
- VALIDATION_ERROR
- MISSING_FIREBASE_TOKEN
- INVALID_FIREBASE_TOKEN
- REVOKED_FIREBASE_TOKEN
- FIREBASE_NOT_CONFIGURED
- FORBIDDEN_ROLE

## 4. POST /api/datasets/upload

**Description:** Upload ASTraM CSV and run validation/cleaning.  
**Authentication:** Level 1 Admin / Control Room Firebase user required.  
**Validation:** CSV only, size limit configured, required columns present.

Response:

```json
{
  "status": "success",
  "rows_loaded": 8173,
  "columns_detected": 46,
  "invalid_rows": 0
}
```

## 5. GET /api/events

**Description:** Paginated event list.
**Authentication:** Level-aware. Public users receive public-safe fields only; officers receive assigned operational fields; admins receive full masked operational fields.

Query parameters:

```text
event_type
event_cause
priority
status
corridor
police_station
zone
junction
requires_road_closure
start_date
end_date
is_peak_hour
limit
offset
```

Response:

```json
{
  "items": [
    {
      "id": "FKID000001",
      "event_type": "unplanned",
      "event_cause_clean": "vehicle_breakdown",
      "latitude": 12.92188,
      "longitude": 77.64516,
      "priority": "High",
      "status": "resolved",
      "corridor": "ORR East 1",
      "police_station": "HSR Layout"
    }
  ],
  "limit": 50,
  "offset": 0,
  "total": 8173
}
```

## 6. GET /api/events/{event_id}

**Description:** Full event dossier.
**Authentication:** Level-aware. Public users receive public advisories only; assigned officers receive officer-safe action plans; admins receive the full internal dossier.
**Authorization note:** Level 2 officers must be assigned to the event, corridor, station, or zone to access event-specific operational details.
**Behavior note:** This is a read-only dossier endpoint. If materialized features, DNA, or predictions are missing, the backend may compute them for the response without persisting new rows during the `GET`.
**Recommendation note:** `prediction` remains the canonical persisted event prediction snapshot. `recommendation` may reflect the latest stored weather-aware planning scenario through its own `risk_summary` and `weather_risk` payloads.

Response includes:

```text
event
features
event_dna
prediction
recommendation
similar_events
citizen_reports
live_updates
map_overlays
```

## 7. GET /api/analytics/summary

**Description:** Dashboard metrics.
**Authentication:** Level 1 Admin / Control Room or Level 2 Registered Police Officer. Public users should use public advisories, not internal analytics.

Response:

```json
{
  "total_events": 8173,
  "planned_events": 467,
  "unplanned_events": 7706,
  "high_priority_events": 5030,
  "road_closure_required": 676,
  "top_causes": [],
  "top_corridors": [],
  "top_police_stations": []
}
```

## 8. GET /api/analytics/hotspots

**Description:** Hotspot clusters and GeoJSON overlays.
**Authentication:** Level 1 Admin / Control Room or Level 2 Registered Police Officer.

Query parameters:

```text
event_cause
priority
requires_road_closure
cluster_type
```

Response:

```json
{
  "hotspots": [
    {
      "location_cluster_id": "CL-001",
      "centroid_latitude": 12.9716,
      "centroid_longitude": 77.5946,
      "cluster_event_count": 146,
      "cluster_risk_score": 88,
      "cluster_top_event_cause": "vehicle_breakdown"
    }
  ],
  "geojson": {}
}
```

## 8.1 GET /api/analytics/model-runs

**Description:** Latest recorded training/inference metadata per model family for internal diagnostics.
**Authentication:** Level 1 Admin / Control Room or Level 2 Registered Police Officer.

Response:

```json
{
  "model_runs": [
    {
      "model_name": "priority_model",
      "model_version": "priority_rf_v1",
      "training_rows": 6536,
      "test_rows": 1634,
      "artifact_available": true,
      "artifact_status": "loaded"
    }
  ]
}
```

## 9. POST /api/events/simulate

**Description:** Create a temporary event and generate intelligence.
**Authentication:** Level 1 Admin / Control Room or Level 2 Registered Police Officer in MVP. Public users cannot create internal simulations.

Request:

```json
{
  "event_type": "planned",
  "event_cause": "procession",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "corridor": "MG Road",
  "police_station": "Example Police Station",
  "zone": "Central Zone",
  "junction": "Example Junction",
  "start_datetime": "2026-06-18T18:00:00",
  "expected_duration_minutes": 120,
  "expected_crowd_size": 5000,
  "weather_condition": "heavy_rain",
  "rain_mm": 12,
  "visibility_m": 700,
  "use_live_weather": false,
  "available_officers": 18,
  "description": "Large procession expected during evening peak"
}
```

Validation:

- latitude -90 to 90
- longitude -180 to 180
- event_type in planned/unplanned
- start_datetime ISO datetime
- weather_condition in allowed enum

Response:

```json
{
  "event_dna": {},
  "similar_event_summary": {},
  "predicted_priority": "High",
  "priority_confidence": 0.84,
  "road_closure_probability": 0.78,
  "estimated_clearance_minutes": 47,
  "clearance_prediction_method": "historical_similarity_or_ml",
  "clearance_confidence": 0.68,
  "clearance_confidence_note": "Estimated clearance time based on reliable ASTraM closed/resolved timestamps under 24 hours.",
  "historical_clearance_range_min": 34,
  "historical_clearance_range_max": 72,
  "estimated_impact_score": 82,
  "impact_category": "Critical",
  "impact_radius_km": 3.0,
  "vehicle_impact_factor": 1.37,
  "vehicle_impact_note": "Heavy vehicle impact adjustment applied using ASTraM vehicle-type clearance patterns.",
  "counterfactual": {
    "baseline_risk_score": 42,
    "event_impact_score": 82,
    "additional_event_delta": 40
  },
  "weather_adjustment": {
    "weather_condition": "heavy_rain",
    "weather_factor": 1.3,
    "rain_mm": 12,
    "visibility_m": 700,
    "low_visibility": true,
    "waterlogging_risk": "elevated",
    "reason_codes": ["rain_or_wet_roads", "heavy_rain_waterlogging_risk", "low_visibility"],
    "source": "manual_simulation_selector",
    "provider": null,
    "provider_status": "manual_override",
    "note": "Weather modifier uses a manual scenario override for MVP planning and remains an operational estimate."
  },
  "recommendations": {},
  "map_overlays": {}
}
```

Road-closure note:

- `road_closure_probability` is the primary signal.
- `predicted_road_closure` is a heuristic operational flag derived from that probability for command-center workflows.

## 10. POST /api/recommendations/event-plan

**Description:** Generate or regenerate response plan.
**Authentication:** Level 1 Admin / Control Room or assigned Level 2 Registered Police Officer.

Request:

```json
{
  "event_id": "SIM-001",
  "available_officers": 18,
  "include_logistics_impact": true,
  "include_emergency_corridor": true,
  "weather_condition": "heavy_rain",
  "rain_mm": 12,
  "visibility_m": 700,
  "use_live_weather": false
}
```

Response:

```json
{
  "event_id": "SIM-001",
  "risk_summary": {
    "impact_score": 82,
    "impact_category": "Critical",
    "road_closure_probability": 0.78,
    "predicted_priority": "High",
    "estimated_clearance_minutes": 47,
    "estimated_radius_km": 3,
    "baseline_risk_score": 42,
    "additional_event_delta": 40,
    "honesty_note": "Recommended actions are dataset-backed operational guidance, not a live city-control guarantee."
  },
  "weather_risk": {
    "weather_condition": "heavy_rain",
    "weather_factor": 1.3,
    "rain_mm": 12,
    "visibility_m": 700,
    "low_visibility": true,
    "waterlogging_risk": "elevated",
    "reason_codes": ["rain_or_wet_roads", "heavy_rain_waterlogging_risk", "low_visibility"],
    "source": "manual_event_plan_override",
    "provider": null,
    "provider_status": "manual_override",
    "note": "Weather modifier uses a manual scenario override for MVP planning and remains an operational estimate."
  },
  "manpower": {
    "recommended_total_officers": 12,
    "deployment_style": "ring_control",
    "reserve_officers": 3,
    "sector_count": 4,
    "available_officers": 18,
    "officer_gap": 0,
    "feasibility_status": "covered",
    "primary_positions": ["incident_core", "upstream_junction", "downstream_release"],
    "reason_codes": ["impact_category", "road_closure_probability", "impact_radius_km"],
    "note": "Recommended staffing is operational guidance, not a shift roster guarantee."
  },
  "barricades": {
    "barricade_level": "extended_buffer_with_slow_speed_channelization",
    "estimated_units": 12,
    "coverage_radius_km": 3,
    "placement_priority": ["incident_core", "upstream_filter", "diversion_split"],
    "reason_codes": ["impact_score", "road_closure_probability", "rain_or_wet_roads", "heavy_rain_waterlogging_risk", "low_visibility"],
    "note": "Barricade guidance is radius-based and should be adapted to field geometry.",
    "field_note": "Increase taper distance and avoid pushing traffic through low-lying road segments."
  },
  "diversions": {
    "strategy": "weather_buffered_hotspot_bypass",
    "corridor_to_protect": "MG Road",
    "diversion_scope": "avoid low-lying approaches and create wider upstream diversion buffers",
    "upstream_focus_points": ["MG Road", "Central zone upstream", "avoid low-lying roads", "advance warning farther upstream"],
    "heavy_vehicle_advisory": "Move heavy vehicles away from low-lying corridors and flooded underpasses before hotspot entry.",
    "reason_codes": ["corridor", "impact_radius_km", "vehicle_mix", "rain_or_wet_roads", "heavy_rain_waterlogging_risk", "low_visibility"],
    "note": "Diversion guidance is advisory and not a citywide routing guarantee.",
    "field_note": "Do not route diversions through low-visibility or waterlogging-prone links without field confirmation."
  },
  "emergency_corridor": {
    "priority": "high_protection",
    "lane_policy": "keep_one_lane_clear",
    "protected_corridor": "MG Road",
    "activation_trigger": "activate when closure likelihood or impact severity is high",
    "authentication_note": "Ambulance verification is future scope; MVP protects corridor advisory only.",
    "reason_codes": ["impact_category", "road_closure_probability"]
  },
  "flipkart_logistics_impact": {
    "impact_level": "high",
    "delivery_risk_window_minutes": 60,
    "affected_radius_km": 3,
    "dispatch_recommendation": "Consider dispatch staggering or alternate approach routing for the active risk window.",
    "warehouse_note": "Use recommendation as a delivery-risk indicator, not as a guaranteed SLA breach forecast.",
    "reason_codes": ["impact_score", "estimated_clearance_minutes"]
  },
  "action_confidence_ledger": [
    {
      "input": "ASTraM historical events",
      "confidence": 0.85,
      "note": "Core event patterns, corridors, and closure history come from the loaded ASTraM dataset.",
      "source": "dataset_history"
    }
  ],
  "recommended_action_summary": "Deploy 12 officers in ring control around MG Road. Use controlled entry exit points and protect primary corridor and push early diversion operations."
}
```

Behavior note:

- If weather fields are supplied, the backend may compute a transient weather-adjusted prediction input for planning.
- The persisted `event_predictions` row remains the canonical prediction snapshot for the event.
- The persisted `event_recommendations` row stores the latest recommendation snapshot, including scenario-specific `risk_summary` and `weather_risk`.

Contract reuse note:

- `GET /api/events/{event_id}` returns the same shape under `recommendation`.
- `POST /api/events/simulate` returns the same shape under `recommendations`.

## 11. POST /api/reports/congestion

**Description:** Submit citizen/field/control-room report.
**Authentication:** Level 3 public allowed for `report_source=citizen`; Level 2 required for `report_source=field_officer`; Level 1 required for `report_source=control_room`.

Request:

```json
{
  "report_source": "citizen",
  "report_type": "road_blockage",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "severity": "High",
  "description": "ಮದುವೆ ಮೆರವಣಿಗೆ ಎರಡು ಲೇನ್‌ಗಳನ್ನು ತಡೆದಿದೆ",
  "event_id": null,
  "language": "kn"
}
```

Rate limit: 10/min/IP in demo.  
Security: sanitize description, reject invalid coordinates, do not auto-officialize citizen reports.

Response:

```json
{
  "status": "accepted",
  "matched_event_id": "EVT-2041",
  "source_language": "kn",
  "translation_status": "translated",
  "translated_description": "Wedding procession has blocked two lanes",
  "location_match_confidence": 0.91,
  "report_confidence": 0.74,
  "impact_score_change": 12,
  "new_alert_level": "Warning",
  "recommended_action": "Move 2 reserve officers to upstream junction and activate Diversion Plan B"
}
```

## 12. POST /api/events/{event_id}/live-update

**Authentication:** Level 2 Registered Police Officer assigned to the event/corridor/station, or Level 1 Admin / Control Room.

Request:

```json
{
  "current_congestion_level": "Critical",
  "field_update": "Crowd spillover near upstream junction",
  "road_closure_active": true,
  "officer_shortage": true,
  "crowd_increase": true,
  "rain_waterlogging": true,
  "new_nearby_incident": false
}
```

Response:

```json
{
  "expected_impact_score": 72,
  "current_impact_score": 88,
  "impact_deviation": 16,
  "alert_level": "Warning",
  "adaptive_action": "Move 2 reserve officers upstream and activate Diversion Plan B"
}
```

## 13. POST /api/events/multi-event-analysis

**Authentication:** Level 1 Admin / Control Room or Level 2 Registered Police Officer.

Request:

```json
{
  "event_ids": ["EVT-1", "EVT-2"],
  "available_officers": 24
}
```

Response:

```json
{
  "conflict_detected": true,
  "combined_risk": "Critical",
  "conflict_signals": [
    "time overlap",
    "shared corridor",
    "diversion route conflict",
    "officer gap"
  ],
  "coordination_plan": []
}
```

## 14. POST /api/events/{event_id}/post-event-report

**Authentication:** Level 1 Admin / Control Room, or assigned Level 2 Registered Police Officer when enabled.
**Behavior note:** Generates and persists an after-action learning snapshot using the stored event, prediction, recommendation, citizen-report, and live-escalation context currently available for the event.

Response:

```json
{
  "event_id": "FKID000001",
  "predicted_impact_score": 78,
  "simulated_actual_impact_score": 94,
  "impact_deviation": 16,
  "final_status": "resolved",
  "event_summary": "...",
  "prediction_summary": "...",
  "recommendation_summary": "...",
  "citizen_report_summary": "...",
  "live_escalation_summary": "...",
  "lessons_learned": "...",
  "future_recommendations": "...",
  "report_json": {},
  "created_at": "2026-06-18T12:34:56Z"
}
```

## 15. POST /api/admin/officers

**Description:** Add a registered police officer for Level 2 access.  
**Authentication:** Level 1 Admin / Control Room Firebase user required.

Request:

```json
{
  "email": "officer.hsr.demo@eventflow.local",
  "firebase_uid": "firebase_uid_created_or_invited_for_officer",
  "officer_id": "BTP-HSR-001",
  "display_name": "Officer Demo",
  "rank": "Traffic Constable",
  "police_station": "HSR Layout",
  "assigned_corridors": ["ORR East 1"],
  "assigned_zones": ["East"]
}
```

Response:

```json
{
  "status": "created",
  "officer_id": "BTP-HSR-001",
  "role": "police_officer",
  "active": true
}
```

## 16. POST /api/officer/login

**Description:** Firebase Auth login is handled in the frontend using Firebase client SDK. This backend endpoint is not required for normal MVP login. If implemented, it should only exchange/verify a Firebase ID token and return the officer profile.

Request:

```json
{
  "firebase_id_token": "eyJhbGciOi..."
}
```

Response:

```json
{
  "role": "police_officer",
  "firebase_uid": "firebase_uid_created_or_invited_for_officer",
  "officer_id": "BTP-HSR-001",
  "police_station": "HSR Layout",
  "assigned_corridors": ["ORR East 1"],
  "assigned_zones": ["East"]
}
```

## 17. GET /api/officer/assignments

**Description:** Return events, routes, reports, and recommendations assigned to the logged-in officer.
**Authentication:** Level 2 Registered Police Officer.

Response:

```json
{
  "officer_id": "BTP-HSR-001",
  "police_station": "HSR Layout",
  "assigned_events": [],
  "assigned_corridors": ["ORR East 1"],
  "assigned_zones": ["East"],
  "pending_report_confirmations": [],
  "map_overlays": {}
}
```

## 18. GET /api/map/config

**Description:** Return frontend-safe map provider configuration.

Response:

```json
{
  "activeProvider": "mapmyindia",
  "primaryProvider": "mapmyindia",
  "fallbackProvider": "osm",
  "mapKeyAvailable": true,
  "creditsBudgetInr": 1000,
  "budgetGuardEnabled": true,
  "fallbackReason": null
}
```

## 19. POST /api/map/route

**Description:** Generate diversion/emergency/logistics route polyline using MapmyIndia when budget and API status allow; otherwise return local fallback route.

Request:

```json
{
  "origin": [77.5946, 12.9716],
  "destination": [77.6850, 12.9308],
  "mode": "driving",
  "purpose": "diversion_plan"
}
```

Response:

```json
{
  "provider": "mapmyindia",
  "polyline": [[77.5946, 12.9716], [77.6100, 12.9600], [77.6850, 12.9308]],
  "distanceMeters": 12400,
  "durationSeconds": 2100,
  "confidence": "provider_route",
  "cached": false
}
```

## 20. POST /api/map/geocode

**Description:** Optional address-to-coordinate lookup through MapmyIndia when enabled. If disabled or credit guard is hit, frontend must support manual coordinate/address entry.

## 21. POST /api/translation/normalize

**Description:** Optional backend-only Google Translate normalization endpoint for report descriptions. Used when Phase 19 is enabled.  
**Authentication:** Level 1/Level 2 for direct testing; report submission may call this internally for public reports.  
**Cost control:** disabled by default, backend credentials only, character budget guarded.

Request:

```json
{
  "text": "ಮದುವೆ ಮೆರವಣಿಗೆ ಎರಡು ಲೇನ್‌ಗಳನ್ನು ತಡೆದಿದೆ",
  "source_language": "kn",
  "target_language": "en",
  "purpose": "citizen_report"
}
```

Response:

```json
{
  "original_text": "ಮದುವೆ ಮೆರವಣಿಗೆ ಎರಡು ಲೇನ್‌ಗಳನ್ನು ತಡೆದಿದೆ",
  "source_language": "kn",
  "target_language": "en",
  "translated_text": "Wedding procession has blocked two lanes",
  "provider": "google",
  "status": "translated",
  "character_count": 38
}
```

Fallback statuses:

- disabled
- budget_blocked
- failed
- source_already_target
