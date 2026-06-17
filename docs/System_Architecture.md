# EventFlow AI System Architecture

## 1. Architecture Goals

EventFlow AI must be modular, explainable, free-tier friendly, and demo-ready. The system must separate map rendering, API orchestration, domain logic, AI/ML inference, database persistence, and report generation.

## 2. High-Level Architecture

```mermaid
flowchart TD
    Admin["Level 1 Admin / Control Room Portal"] --> Firebase["Firebase Auth"]
    Officer["Level 2 Registered Police Officer Portal"] --> Firebase
    Firebase --> Auth["FastAPI Access Control Service"]
    Public["Level 3 Public / Citizen Portal"] --> Auth
    A["ASTraM CSV / Demo Data"] --> B["FastAPI Data Ingestion"]
    B --> C["Cleaning + Feature Engineering"]
    C --> D["Supabase PostgreSQL Free Tier"]
    D --> E["Event DNA Service"]
    D --> F["Hotspot Service"]
    D --> G["Similar Event Service"]
    E --> H["Hybrid AI Planning Engine"]
    F --> H
    G --> H
    H --> I["Prediction Services"]
    H --> J["Impact Scoring"]
    H --> K["Recommendation Engine"]
    K --> L["Manpower Plan"]
    K --> M["Barricade Plan"]
    K --> N["Diversion Plan"]
    K --> O["Emergency Corridor Advisory"]
    K --> P["Flipkart Logistics Impact"]
    Q["Citizen / Field Reports"] --> Auth
    Auth --> R["Verification Service"]
    R --> H
    R --> S["Live Escalation Service"]
    S --> K
    K --> T["Post-Event Learning"]
    U["Next.js Web App"] --> Auth
    Auth --> V["FastAPI REST APIs"]
    V --> D
    V --> H
    U --> W["Map Adapter: MapmyIndia primary with 1000 INR credits, OSM fallback"]
```

## 3. Layer Responsibilities

| Layer | Responsibility |
|---|---|
| Client Layer | Three portals: admin/control room, registered police officer, public/citizen |
| Web Layer | Next.js routing, role-aware dashboards, officer portal, citizen report form, map panels, API hooks |
| Mobile Layer | MVP uses responsive PWA page; native app is future scope |
| API Layer | FastAPI REST endpoints, Firebase ID-token verification, three-level authorization, error handling |
| Service Layer | Event DNA, predictions, recommendations, reports, reports verification |
| Domain Layer | Event, hotspot, report, prediction, recommendation, playbook, officer, assignment concepts |
| Business Logic Layer | Risk scoring, confidence scoring, weather modifiers, multi-event coordination |
| Data Layer | Supabase PostgreSQL, SQLAlchemy repositories, Alembic migrations |
| AI Layer | scikit-learn models, DBSCAN clustering, weighted similarity, rule-based planning |
| Infrastructure Layer | Vercel frontend, Render/Railway backend, Supabase DB, GitHub Actions |

## 4. API Request Flow

```mermaid
sequenceDiagram
    participant User
    participant Web as Next.js Web
    participant API as FastAPI
    participant Service as Domain Services
    participant DB as Supabase PostgreSQL
    User->>Web: Submit event simulation
    Web->>API: POST /api/events/simulate
    API->>API: Validate Pydantic schema
    API->>Service: Generate Event DNA + predictions
    Service->>DB: Read historical events/features
    DB-->>Service: Historical patterns
    Service-->>API: Impact + recommendations + map overlays
    API-->>Web: Simulation response
    Web-->>User: Render intelligence panels and map
```

## 5. Data Processing Flow

```mermaid
flowchart LR
    A["Raw CSV"] --> B["Validate required columns"]
    B --> C["Parse timestamps"]
    C --> D["Normalize event causes"]
    D --> E["Mask sensitive fields"]
    E --> F["Derive time/location features"]
    F --> G["Generate risk aggregates"]
    G --> H["Train or fit models"]
    H --> I["Persist events/features/models metadata"]
```

## 6. Event Flow

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Simulated: Generate intelligence
    Simulated --> Active: Save/activate event
    Active --> Warning: Citizen reports or live update
    Warning --> Critical: High deviation or closure active
    Critical --> Stabilized: Adaptive action applied
    Stabilized --> Closed: Event ended
    Closed --> Learned: Post-event report generated
```

## 7. User Journey Flow

```mermaid
flowchart TD
    A["Open Command Center"] --> B["Inspect hotspots and active alerts"]
    B --> C["Create event in Simulation Lab"]
    C --> D["Generate Event DNA"]
    D --> E["Review predictions and recommendations"]
    E --> F["Open Map Intelligence"]
    F --> G["Submit citizen / field report"]
    G --> H["Live escalation updates plan"]
    H --> I["Close event"]
    I --> J["Generate post-event playbook"]
```

## 8. Notification Flow

MVP uses in-app alerts only. External SMS, WhatsApp, push notifications, and official police dispatch notifications are future scope.

```mermaid
flowchart LR
    A["Report / live update / multi-event conflict"] --> B["Escalation Service"]
    B --> C["Alert Level"]
    C --> D["Command Center Urgent Queue"]
    C --> E["Event Detail Timeline"]
    C --> F["Map marker pulse"]
```

## 9. Deployment Architecture

```mermaid
flowchart TD
    Dev["Developer Machine"] --> Git["GitHub"]
    Git --> Actions["GitHub Actions CI"]
    Actions --> Vercel["Vercel Free Tier: Next.js"]
    Actions --> Backend["Render/Railway Free Tier: FastAPI"]
    Backend --> DB["Supabase PostgreSQL Free Tier"]
    Vercel --> Backend
```

## 10. Monitoring Architecture

```mermaid
flowchart LR
    A["Frontend Web Vitals"] --> B["Console / Free Analytics"]
    C["FastAPI Logs"] --> D["Platform Logs"]
    E["Health Endpoint"] --> F["UptimeRobot Free Monitor"]
    G["Model Run Metrics"] --> H["model_runs table"]
    I["API Errors"] --> J["structured JSON logs"]
```

## 11. CI/CD Pipeline

```mermaid
flowchart LR
    A["Push / PR"] --> B["Install deps"]
    B --> C["Frontend lint/build"]
    B --> D["Backend tests"]
    D --> E["API contract smoke tests"]
    C --> F["Deploy frontend"]
    D --> G["Deploy backend"]
    G --> H["Run health check"]
```
