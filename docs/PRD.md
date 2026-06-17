# EventFlow AI Product Requirements Document

## 1. Hackathon Project Overview

**Project name:** EventFlow AI  
**Subtitle:** Predictive Traffic Command Twin for Event-Driven Congestion  
**Hackathon:** Flipkart Gridlock 2.0 Phase 2  
**Theme:** Event-Driven Congestion, Planned and Unplanned  
**Problem domain:** Bengaluru urban traffic operations  
**Primary dataset:** ASTraM anonymized Bengaluru Traffic Police event data  
**Partners considered:** Bengaluru Traffic Police / ASTraM, MapmyIndia / Mappls, Flipkart  
**API policy:** base MVP uses free APIs, open-source tools, free tiers, or hackathon-provided partner access. Optional Phase 19 can use Google Translate API only when explicitly enabled with backend credentials and budget guardrails.  

**One-line pitch:** EventFlow AI converts historical Bengaluru traffic events, live citizen/field reports, weather context, and map intelligence into police-ready event response plans for manpower, barricading, diversion, escalation, and post-event learning.

**Elevator pitch:** Bengaluru traffic often breaks down during rallies, processions, festivals, construction, accidents, breakdowns, waterlogging, and sudden crowd movement. EventFlow AI helps traffic authorities move from reactive response to predictive command. It creates an Event DNA for every incident, retrieves similar historical ASTraM events, predicts operational urgency and road closure likelihood, estimates event-driven impact, recommends risk-aware manpower/barricade/diversion plans, adapts during live escalation, and generates a reusable post-event playbook.

## 2. Executive Summary

EventFlow AI is an AI-powered traffic command copilot for Bengaluru event-driven congestion. It is not a generic dashboard or route finder. It is a map-first operational planning system built around the loop:

```text
Predict -> Plan -> Monitor -> Adapt -> Learn
```

The product helps answer:

- What event is happening?
- Where is it happening?
- Why is it risky?
- Which similar events happened before?
- Is road closure likely?
- Which corridors, junctions, and police stations are affected?
- How many officers may be needed?
- Where should officers and barricades be placed?
- Which simplified diversion plan should be prepared?
- Are multiple events conflicting?
- Is weather changing the physical response plan?
- What should be learned after the event?

## 3. Problem Statement

Planned and unplanned events in Bengaluru create localized traffic breakdowns. Traffic authorities often need to make decisions about severity, road closure, manpower, barricading, diversion, and live escalation using limited time and experience-driven judgment.

The official challenge asks:

> How can historical and real-time data be used to forecast event-related traffic impact and recommend optimal manpower, barricading, and diversion plans?

For dataset honesty, EventFlow AI does not claim exact traffic speed, exact vehicle delay, exact queue length, or mathematically optimal manpower because the provided ASTraM dataset does not include traffic speed, traffic volume, actual manpower deployment, barricade history, or verified diversion success. The product uses safer labels:

- Estimated traffic impact
- Operational urgency prediction
- Road closure likelihood
- Estimated clearance time
- Vehicle impact factor
- Risk-aware manpower recommendation
- Data-assisted barricading plan
- Simplified diversion recommendation
- Simulated live escalation
- Post-event learning report

## 4. Challenge And Opportunity

### Current Pain Points

- Event impact is not quantified in advance.
- Manpower deployment is often experience-driven.
- Barricading and diversion are prepared reactively.
- Small or sudden events may be reported late through phone calls.
- Field updates and citizen signals are not consistently converted into action.
- There is no strong after-action learning loop.
- Multiple simultaneous events may compete for roads, diversion routes, and officers.

### Opportunity

The ASTraM dataset contains real Bengaluru event records with event type, event cause, location, corridor, police station, priority, closure flag, status, and timestamps. These can support event analytics, hotspot discovery, operational urgency prediction, road closure likelihood, similar-event retrieval, and explainable response recommendations.

Dataset realities observed in the full uploaded ASTraM CSV:

- Total rows: `8173`.
- `requires_road_closure = TRUE`: `676` rows, about `8.27%`. This is usable for historical closure-rate analysis, but weak for a standalone reliable classifier.
- `end_datetime` is null for `7683` rows, about `94%`. Duration features must use a documented timestamp fallback chain.
- `closed_datetime` is present for `3141` rows and `resolved_datetime` for `74` rows.
- `description` contains non-ASCII/Kannada-script text in `904` rows, about `11.06%`. Text handling must detect language and normalize safely before Event DNA or explanations use description context.

MapmyIndia/Mappls is the primary geospatial layer for MVP because the team has `1000 INR` credits available. OpenStreetMap/MapLibre remains an automatic fallback for missing keys, API failures, or credit guardrails. Flipkart relevance is added through a logistics impact panel that estimates delivery corridor risk.

## 5. Proposed Solution

EventFlow AI is a web-based command center with optional PWA-style citizen/field report screens.

Core capabilities:

1. Ingest and clean ASTraM event data.
2. Detect description language and create a safe English feature summary for Kannada/non-English rows using static/free normalization in base MVP, or optional Google Translate in Phase 19.
3. Generate Event DNA for each event.
4. Detect operational risk hotspots.
5. Retrieve similar historical events.
6. Predict operational urgency from historical patterns.
7. Estimate road-closure likelihood primarily through explainable rules and historical closure rates, with ML as supporting evidence only.
8. Estimate clearance time with confidence and historical range using reliable `closed_datetime`/`resolved_datetime` patterns.
9. Estimate event impact score and impact radius.
10. Compare baseline risk with event-driven risk.
11. Recommend manpower deployment.
12. Recommend barricade/checkpoint placement.
13. Recommend simplified diversion plans using a demo road graph.
14. Verify citizen/field reports using confidence scoring.
15. Apply weather-traffic correlation rules.
16. Detect simultaneous multi-event conflicts.
17. Add emergency corridor advisory.
18. Estimate Flipkart logistics impact.
18. Simulate live escalation and adaptive response.
19. Generate post-event learning reports and future playbooks.

## 6. Innovation And Differentiation

### Event DNA

Every event becomes an operational fingerprint:

```text
event type + cause + time + location + corridor + police station + hotspot + weather + similar history + closure risk
```

This makes the AI explainable and judge-friendly.

Raw `description` text is not blindly used in Event DNA. The dataset includes Kannada/non-English descriptions, so the pipeline must:

- preserve the raw description for audit/debug,
- detect language/script,
- create `description_for_features` using static phrase mapping and/or free/open-source transliteration libraries,
- mark the normalization method and confidence,
- prefer structured fields (`event_cause`, `corridor`, `police_station`, `junction`, timestamps, closure flag) when text normalization confidence is low.

### Similar Event Memory

For a new event, the system retrieves past ASTraM events with similar cause, location, corridor, police station, time band, and closure/priority pattern.

Example:

```text
This new procession is similar to 8 previous public-movement events in nearby high-risk corridors.
Historical high-priority rate: 81%
Historical road-closure rate: 62%
```

### Counterfactual Impact

The product shows:

```text
Baseline risk at this location/time: 41
Predicted event-driven risk: 78
Additional event impact: +37
```

### Action Confidence Ledger

Every recommendation includes reason codes:

```text
Deploy 3 officers near upstream junction because road closure probability is high, the event is during evening peak, the corridor is a hotspot, and similar events escalated.
```

### Citizen / Field Report Verification

Users can mark events, but reports are not trusted blindly. Multiple nearby reports, field officer source, hotspot proximity, and police confirmation increase confidence.

### Weather-Adjusted Barricading

Rain and waterlogging do not only increase risk; they change the physical response plan. Barricades move upstream, reflective/advance warning checkpoints are added, low-lying diversions are avoided, and emergency access gates are protected.

### Multi-Event Coordination

When 2+ events happen simultaneously, the system checks time overlap, impact radius overlap, shared corridors, diversion conflicts, and manpower pressure.

### Post-Event Playbook

After closure, the system generates future recommendations:

```text
For future evening processions near this corridor, activate diversion checkpoints 30 minutes earlier and keep 2 reserve officers upstream.
```

## 7. Hackathon Theme Alignment

The project aligns directly with event-driven congestion by forecasting impact from historical and real-time data and recommending operational response plans. It also aligns with partner strengths:

- **BTP / ASTraM:** real event intelligence and field context.
- **MapmyIndia / Mappls:** primary geospatial base map, routing context, corridor visualization, and operational overlays using the available `1000 INR` credits with OSM/MapLibre fallback.
- **Flipkart:** logistics impact layer showing delivery corridor risk and dispatch advisories.

## 8. Target Users And Personas

### Three-Level Access Model

EventFlow AI must be presented as a three-level civic traffic response system, not a single flat dashboard.

| Level | Portal | Primary Users | MVP Authentication | Production/Future Authentication | What They Can Access |
|---|---|---|---|---|---|
| Level 1 | Admin / Control Room Portal | Control room admin, senior operator, system owner | Firebase Auth email/password + backend admin/control-room role | Optional official BTP SSO/custom claims later | Officer registration, dataset load/upload, planned event creation, full command dashboard, official approvals, demo reset |
| Level 2 | Registered Police Officer Portal | Field traffic officers and station/corridor officers | Firebase Auth email/password + backend officer assignment checks | Optional official BTP SSO/custom claims later | Assigned events, recommended routes/diversions, field updates, report confirmation, officer-safe map overlays |
| Level 3 | Public / Citizen Portal | Citizens, commuters, delivery partners, public viewers | Public access with rate limits and validation | Optional public account or anonymous reporting with abuse controls | Public advisories, safe map information, citizen reports, multilingual report form |

Access must be role-aware:

- Public users must not see officer identities, exact manpower counts, internal barricade strategy, sensitive ASTraM fields, or control-room confidence internals.
- Registered officers can see operational recommendations only for assigned stations/corridors/events.
- Admin/control-room users can manage officer registration and all official demo/admin actions.
- The MVP should use Firebase Auth for Level 1 and Level 2 login, while keeping Level 3 public access open and rate-limited.
- Firebase proves identity; FastAPI/PostgreSQL still enforce EventFlow roles, officer active status, and station/corridor/event assignments.

### Traffic Control Room Operator

- **Background:** monitors active incidents and coordinates field response.
- **Goals:** quickly identify critical events and recommended actions.
- **Pain points:** too many incidents, limited prioritization, delayed updates.
- **Benefits:** urgent action queue, event impact score, live escalation alerts.

### Senior Traffic Planning Officer

- **Background:** prepares for planned events and reviews operations.
- **Goals:** pre-plan manpower, barricades, diversions, and future readiness.
- **Pain points:** planning relies on memory and manual experience.
- **Benefits:** similar event memory, risk forecasts, post-event playbooks.

### Field Traffic Officer

- **Background:** manages specific junctions and reports live conditions.
- **Goals:** know assigned location, reason, and escalation action.
- **Pain points:** unclear why deployment is needed or when to adapt.
- **Benefits:** officer portal, assigned action, officer-safe routing/diversion overlays, field report confirmation, adaptive recommendations.

### Citizen / Delivery Partner

- **Background:** reports sudden road blockage, accident, or congestion.
- **Goals:** submit quick report in local language.
- **Pain points:** calling 100/112 may take time; small events go unreported.
- **Benefits:** fast report form, multilingual labels, confidence-based escalation.

### Hackathon Judge

- **Background:** evaluates feasibility, innovation, relevance, and impact.
- **Goals:** understand problem, see working demo, trust data honesty.
- **Benefits:** complete loop from prediction to post-event learning.

## 9. User Stories

### Core MVP User Stories

- As an operator, I can load demo ASTraM data and see summary metrics.
- As an operator, I can view events and hotspots on a map.
- As a planner, I can simulate a planned or unplanned event.
- As a planner, I can see Event DNA and similar historical events.
- As a planner, I can see urgency and road closure predictions with reasons.
- As a planner, I can get manpower, barricade, and diversion recommendations.
- As a field officer/citizen, I can submit a congestion/event report.
- As an operator, I can see report confidence and matched event/hotspot.
- As an operator, I can trigger live escalation and receive adaptive action.
- As a planner, I can generate a post-event learning report.

### Non-Functional User Stories

- As an operator, dashboard pages should load within 5 seconds.
- As a judge, demo mode should run without manual code edits.
- As a security reviewer, sensitive identifiers should be masked.
- As an evaluator, each AI output should show confidence and reason codes.
- As a user, all estimated outputs should be clearly labelled.

### Edge Case User Stories

- If zone/junction/route_path is missing, the system falls back to coordinates, corridor, police station, and hotspot cluster.
- If map provider fails, the dashboard shows non-map recommendations and a retry state.
- If model artifact is missing, the backend falls back to rule-based scoring with lower confidence.
- If weather API fails, manual weather selector remains available.
- If a citizen report is unverified, it stays in low-confidence state and does not automatically become official.

### Accessibility User Stories

- Risk badges must include text and icon/shape, not only color.
- All forms must be keyboard-usable.
- Citizen report screen must be responsive on mobile.
- Minimum body font size should be 13px, preferably 14px.

## 10. MVP Scope

### In Scope

- Web command center
- Three-level portal model: admin/control room, registered police officer, public/citizen
- Firebase Auth-backed admin and police officer login
- Admin-created Firebase-linked officer accounts and officer assignment model
- Responsive citizen/field report page
- Data cleaning and feature engineering
- Supabase PostgreSQL free tier storage
- FastAPI service layer
- MapmyIndia/Mappls primary integration using available `1000 INR` credits, with OSM/MapLibre fallback
- Urgency and road closure prediction
- Event DNA and similar event memory
- Hotspot heatmap
- Recommendation engines
- Weather risk modifier
- Multi-event coordination
- Emergency corridor advisory
- Flipkart logistics impact layer
- Post-event report
- Demo mode

### Out Of Scope

- Mandatory paid APIs; Google Translate is optional Phase 19 only
- Native mobile app
- Real ambulance authentication
- Real 108/112/hospital dispatch integration
- Real traffic speed feed
- CCTV/computer vision
- Full city-scale routing
- Production RBAC and official police integration
- Phone OTP authentication in MVP

## 11. Demo Scenario

1. Open Command Center.
2. Show ASTraM event summary and risk hotspots.
3. Open Simulation Lab.
4. Create planned procession near a high-risk corridor during evening peak.
5. Generate Event DNA.
6. Show similar historical events and closure/high-priority rates.
7. Show urgency, road closure likelihood, and impact score.
8. Show counterfactual baseline vs event impact.
9. Show manpower, barricade, diversion, emergency corridor, and Flipkart logistics panels.
10. Submit multiple citizen reports for road blockage.
11. Show confidence rising and live alert escalation.
12. Activate heavy rain modifier; show barricades moving upstream and route switching.
13. Run multi-event coordination with another construction event.
14. Show combined risk and coordinated response plan.
15. Mark event closed.
16. Generate post-event learning dashboard and future playbook.

## 12. Success Metrics And KPIs

- Demo dataset loads successfully.
- Event simulation completes under 3 seconds.
- Event plan generation completes under 5 seconds.
- Dashboard initial load under 5 seconds.
- Map layer toggle under 2 seconds.
- At least 5 similar events retrieved where available.
- Every recommendation has reason codes.
- Citizen report confidence updates after multiple reports.
- Post-event report generated successfully.
- No sensitive raw identifiers exposed.
- Zero paid API dependencies.

## 13. Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| No real traffic speed data | Exact congestion prediction unsupported | Use estimated impact score |
| No manpower ground truth | ML manpower model unsupported | Use explainable rules |
| Sparse route_path | Full routing unsupported | Use simplified graph |
| Kannada/non-English descriptions | Bad Event DNA text context | Detect script, preserve raw text, use free/static normalization in base MVP, optionally use Google Translate with budget guardrails in Phase 19, and down-weight low-confidence text |
| `end_datetime` mostly null | Wrong duration features | Use documented timestamp fallback: `end_datetime`, then `closed_datetime`, then `resolved_datetime`, else duration unknown |
| Road closure class imbalance | Poor closure recall from standalone ML | Make rule-based/historical closure scoring the primary MVP output; use class-weighted ML only as supporting signal with PR-AUC/recall reporting |
| MapmyIndia credit/key/API issue | Demo risk | Use provider adapter, budget guardrails, route caching, and OSM/MapLibre fallback |
| Weather API unavailable | Demo risk | Manual weather selector |
| Too broad scope | Incomplete prototype | Prioritize end-to-end demo loop |

## 14. Expected Impact

### User Benefits

- Faster event understanding.
- Earlier action planning.
- Better field coordination.
- Clearer post-event learning.

### Business Benefits

- Flipkart and logistics operators can see at-risk delivery corridors.
- Dispatch windows can be adjusted around event risk.

### Community Benefits

- Citizens and field officers become verified traffic sensors.
- Emergency corridors are protected.
- Public advisories can be generated earlier.

### Industry Impact

EventFlow AI can become a reusable civic-tech pattern for event-driven urban mobility management.
