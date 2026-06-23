# Sanchar Sarthi - Architecture & Flow Diagrams

This document serves as the master catalog for all system architecture and technical flow diagrams within Sanchar Sarthi. The core README has been simplified to only show the top-level architecture, while detailed operational flows are documented below.

---

## 1. System Architecture
Provides a high-level overview of the entire Sanchar Sarthi platform, showing how the Frontend, Backend, ML Models, and Database interact.
![System Architecture](./FlowDiagrams%20%26%20Architecture/SystemArchitecture.jpeg)

---

## 2. End-To-End Operating Loop
Illustrates the continuous operational cycle of the platform: Report -> Verify -> Understand -> Predict -> Plan -> Monitor -> Learn.
![End-To-End Operating Loop](./FlowDiagrams%20%26%20Architecture/End-To-End%20Operating%20Loop.png)

---

## 3. Backend Request Path
Maps the journey of an HTTP request from the Nginx proxy through FastAPI routers, into the core service layer, and finally to the database.
![Backend Request Path](./FlowDiagrams%20%26%20Architecture/Backend%20Request%20Path.png)

---

## 4. Entity Relationship View
Displays the core database schema and how crucial entities like `Event`, `CitizenReport`, and `HotspotCluster` relate to each other.
![Entity Relationship View](./FlowDiagrams%20%26%20Architecture/Entity%20Relationship%20View.png)

---

## 5. Event DNA Generation Flow
Shows how raw incident data is processed and summarized into a core "Event DNA" profile that describes the historical context and cause.
![Event DNA Generation Flow](./FlowDiagrams%20%26%20Architecture/Event%20DNA%20Generation%20Flow.png)

---

## 6. Event Dossier Assembly
Breaks down how the system compiles data from multiple sources (live updates, DNA, predictions) into a single operational dossier for police officers.
![Event Dossier Assembly](./FlowDiagrams%20%26%20Architecture/Event%20Dossier%20Assembly.png)

---

## 7. Foundation Flow
Details the basic lifecycle of an incident in the foundation layer, from intake to verification to status updates.
![Foundation Flow](./FlowDiagrams%20%26%20Architecture/Foundation%20Flow.png)

---

## 8. Live Escalation Flow
Explains how field officers report live updates, and how those updates feed back into the system to recalculate priorities and impact.
![Live Escalation Flow](./FlowDiagrams%20%26%20Architecture/Live%20Escalation%20Flow%20diagram.png)

---

## 9. ML Lifecycle Flow
Maps out the machine learning pipeline: from data extraction and feature engineering to model training, evaluation, and deployment.
![ML Lifecycle Flow](./FlowDiagrams%20%26%20Architecture/ML%20lifecycle%20flow%20diagram.png)

---

## 10. Map Provider Decision Flow
Visualizes the fallback logic used by the Spatial Intelligence layer to choose between primary map providers (like MapmyIndia) and backups.
![Map Provider Decision Flow](./FlowDiagrams%20%26%20Architecture/Map%20Provider%20Decision%20Flow%20diagram.png)

---

## 11. Multi-Event Analysis Flow
Demonstrates how the system detects spatial and temporal conflicts when multiple traffic events occur simultaneously in the same corridor.
![Multi-Event Analysis Flow](./FlowDiagrams%20%26%20Architecture/Multi-Event%20Analysis%20Flow%20diagram.png)

---

## 12. Post-Event Learning Sequence Flow
Shows the automated after-action report generation process, where resolved events are analyzed for lessons learned to improve future AI recommendations.
![Post-Event Learning Sequence Flow](./FlowDiagrams%20%26%20Architecture/Post-Event%20Learning%20sequence%20flow.png)

---

## 13. Product Surface Map
Outlines the frontend Next.js architecture, detailing which user groups (Public, Admin, Control Room) have access to which pages.
![Product Surface Map](./FlowDiagrams%20%26%20Architecture/Product%20Surface%20Map.png)

---

## 14. Raw To Stored Flow
Explains the data ingestion pipeline, showing how raw CSV dumps or API payloads are cleaned, normalized, and stored in the database.
![Raw To Stored Flow](./FlowDiagrams%20%26%20Architecture/Raw%20To%20Stored%20Flow.png)

---

## 15. Runtime Layering
Displays the structural layering of the application at runtime, separating the Gateway, Application logic, Data layer, and Infrastructure.
![Runtime Layering](./FlowDiagrams%20%26%20Architecture/Runtime%20Layering.png)

---

## 16. Service Interaction Diagram
Visualizes the internal method calls and dependencies between different backend services (e.g., how the Recommendation Service relies on the Prediction Service).
![Service Interaction Diagram](./FlowDiagrams%20%26%20Architecture/Service%20Interaction%20Diagram.png)

---

## 17. Simulation Flow
Shows the logic path for the internal Simulation Tool, allowing admins to test hypothetical traffic scenarios against the trained models.
![Simulation Flow](./FlowDiagrams%20%26%20Architecture/Simulation%20Flow.png)

---

## 18. Translational Flow
Details the multilingual architecture, showing how user inputs are translated to English for processing, and then translated back to regional languages for display.
![Translational Flow](./FlowDiagrams%20%26%20Architecture/Translational%20Flow.png)

---

## 19. Recommendation Orchestration
Maps how the Recommendation Engine synthesizes predictions and Event DNA to generate actionable deployment plans (barricades, diversions, manpower).
![Recommendation Orchestration](./FlowDiagrams%20%26%20Architecture/recommendation%20orchestration.png)

---

## 20. Authentication Flow
Explains the Firebase-based authentication cycle, showing how JWT tokens are issued, passed via headers, and validated by the backend middleware.
![Authentication Flow](./FlowDiagrams%20%26%20Architecture/Authentication%20Flow%20diagram.png)
