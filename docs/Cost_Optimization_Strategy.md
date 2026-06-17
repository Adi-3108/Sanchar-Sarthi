# EventFlow AI Cost Optimization Strategy

## 1. Cost Principle

The base MVP must run on free APIs, free tiers, open-source libraries, and local/demo data. Phase 19 adds optional Google Translate support and must remain disabled unless the team intentionally enables Google Cloud credentials, billing/free credits, and budget guardrails.

## 2. Cost-Saving Decisions

| Area | Decision | Cost Benefit |
|---|---|---|
| Maps | MapmyIndia primary with 1000 INR credits, OSM fallback safety mode | uses available credits while preventing demo failure |
| Routing | simplified NetworkX graph | avoids paid routing APIs |
| Weather | Open-Meteo/manual selector | avoids paid weather APIs |
| Database | Supabase free PostgreSQL | avoids infra cost |
| Frontend | Vercel free tier | free hosting |
| Backend | Render/Railway free tier | free demo hosting |
| ML | scikit-learn/joblib | no paid model API |
| Monitoring | UptimeRobot/platform logs | free observability |

## 3. Runtime Optimization

- Precompute hotspots.
- Cache dashboard summary.
- Paginate event queries.
- Avoid expensive map operations on every render.
- Cache MapmyIndia route/geocode responses.
- Do not call MapmyIndia APIs on map pan/zoom.
- Disable optional distance matrix unless needed for demo.
- Track MapmyIndia estimated usage against `MAPMYINDIA_CREDIT_BUDGET_INR=1000`.
- Use model artifacts instead of retraining during requests.
- Use manual/demo weather mode during judging.

## 4. Future Cost Controls

- Add rate limits.
- Use batch processing for reports.
- Archive old events.
- Cache common geospatial queries.
- Keep paid integrations optional adapters only.
