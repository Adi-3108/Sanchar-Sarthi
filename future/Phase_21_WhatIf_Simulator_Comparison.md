# PHASE 21 â€” "What-If" Simulator Comparison

## Phase Overview

Build a side-by-side scenario comparison tool that allows judges and operators to run two simulation scenarios simultaneously â€” for example, "What if we deploy 3 officers vs 5 officers?" â€” and display the impact score difference. Uses two parallel API calls with different manpower inputs to demonstrate resource optimization.

This phase is part of EventFlow AI, a predictive traffic command twin for Bengaluru event-driven congestion. The project uses ASTraM historical event data, FastAPI, Next.js, Supabase PostgreSQL free tier, explainable AI/rule-based planning, MapmyIndia/Mappls primary integration using available 1000 INR credits, Mappls-only map policy, and only free/open-source APIs or services.

---

## Why This Phase Exists

- **Problem being solved:** Traffic operators and judges need to compare different resource deployment strategies before committing personnel and equipment.
- **User need addressed:** Judges will ask "what's the difference between 3 vs 5 officers?" â€” this phase answers with visual side-by-side impact comparison.
- **Business requirement satisfied:** Demonstrates decision support innovation, judge-friendly UX, and cost-benefit analysis capability for Flipkart Gridlock 2.0 evaluation.
- **Why now:** This phase builds on completed simulation engine (Phase 9), adding comparative analytics that support evidence-based decision making.
- **How it contributes:** It strengthens EventFlow AI as a decision support system by quantifying the marginal value of additional resources.

---

## Original Intent Preservation

### Original Problem

Bengaluru event-driven congestion needs data-backed planning for impact, manpower, barricading, diversions, live escalation, and post-event learning. Resource allocation requires cost-benefit analysis.

### User Pain Point

Traffic response teams often over-deploy or under-deploy resources due to lack of comparative analysis tools. Users need a "what-if" simulator to test scenarios before deployment.

### Product Goal

Deliver this capability: Accept two simulation configurations, run them in parallel via existing simulation API, and display side-by-side comparison of impact scores, officer utilization, and cost metrics.

### Architecture Goal

Maintain backend-owned business logic, frontend-only rendering/API consumption, database persistence through Supabase PostgreSQL, and map provider independence. Reuse existing simulation endpoint.

### Security Goal

Protect sensitive ASTraM fields, avoid frontend database credentials, enforce three-level access, validate all inputs, rate-limit risky endpoints.

### Scalability Goal

Run two simulations concurrently without blocking. Cache results for repeated comparisons.

### Performance Goal

Dual simulation requests must complete within 6 seconds total (3 seconds each, run in parallel).

---

## Expected Outcome

After completion:

- **New functionality:** Side-by-side comparison of two simulation scenarios with different resource configurations.
- **New APIs:** Reuses existing POST /api/events/simulate endpoint, no new backend APIs required.
- **New workflows:** Operators configure Scenario A (3 officers) and Scenario B (5 officers), click "Compare", view impact delta, cost difference, and recommendation.
- **New capabilities:** Scenario comparison, resource optimization analytics, marginal impact analysis
- **New infrastructure:** frontend/app/command-center/components/WhatIfComparison.tsx; frontend/lib/hooks/useSimulationComparison.ts
- **New data models:** No new tables required; uses existing simulation endpoint

---

## Full Implementation Requirements

Implementation agents must create executable production-ready source files for every path listed in this phase.

Required implementation standards:

- Complete imports, classes, interfaces, functions, DTOs, models, controllers, services, repositories, middleware, tests, and configuration must be written by the implementation agent.
- No paid APIs may be introduced.
- No placeholder or TODO code may be committed.
- All code must be directly executable in the repository.
- All outputs must preserve EventFlow AI's dataset-honest wording: Dataset-backed, Predicted, Estimated, Recommended, Simulated, or Future integration.

### Exact Repository Paths For This Phase

- frontend/app/command-center/components/WhatIfComparison.tsx
- frontend/app/command-center/components/ScenarioConfig.tsx
- frontend/lib/hooks/useSimulationComparison.ts

---

## Implementation Code Snippets

### `frontend/app/command-center/components/WhatIfComparison.tsx`
```tsx
'use client';

import { useState } from 'react';
import { useSimulationComparison } from '@/lib/hooks/useSimulationComparison';
import ScenarioConfig from './ScenarioConfig';
import { ArrowLeftRight, TrendingUp, Users, DollarSign, AlertCircle } from 'lucide-react';

interface SimulationConfig {
  event_id?: string;
  hypothetical_event?: {
    event_type: string;
    location: { latitude: number; longitude: number };
    start_datetime: string;
  };
  officer_count: number;
  barricade_count: number;
  diversion_count: number;
}

export default function WhatIfComparison() {
  const [scenarioA, setScenarioA] = useState<SimulationConfig>({
    hypothetical_event: {
      event_type: 'breakdown',
      location: { latitude: 12.9716, longitude: 77.5946 },
      start_datetime: new Date().toISOString()
    },
    officer_count: 3,
    barricade_count: 5,
    diversion_count: 2
  });

  const [scenarioB, setScenarioB] = useState<SimulationConfig>({
    hypothetical_event: {
      event_type: 'breakdown',
      location: { latitude: 12.9716, longitude: 77.5946 },
      start_datetime: new Date().toISOString()
    },
    officer_count: 5,
    barricade_count: 8,
    diversion_count: 3
  });

  const { data, isLoading, error, compare } = useSimulationComparison();

  const handleCompare = () => {
    compare(scenarioA, scenarioB);
  };

  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ArrowLeftRight className="w-6 h-6 text-blue-600" />
          What-If Scenario Comparison
        </h2>
        <p className="text-gray-600 mt-1">Compare different resource deployment strategies side-by-side</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ScenarioConfig
          title="Scenario A"
          config={scenarioA}
          onChange={setScenarioA}
          color="blue"
        />
        <ScenarioConfig
          title="Scenario B"
          config={scenarioB}
          onChange={setScenarioB}
          color="green"
        />
      </div>

      <div className="flex justify-center">
        <button
          onClick={handleCompare}
          disabled={isLoading}
          className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Comparing Scenarios...' : 'Compare Scenarios'}
        </button>
      </div>

      {error && (
        <div className="border rounded-lg p-4 bg-red-50 border-red-200">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="w-5 h-5" />
            <span>Comparison failed: {error.message}</span>
          </div>
        </div>
      )}

      {data && (
        <div className="border rounded-lg p-6 bg-white shadow-lg">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Comparison Results</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-blue-700 mb-2">
                <TrendingUp className="w-5 h-5" />
                <span className="font-semibold">Impact Score Delta</span>
              </div>
              <div className="text-3xl font-bold text-blue-900">
                {data.impact_delta > 0 ? '+' : ''}{data.impact_delta.toFixed(1)}%
              </div>
              <p className="text-sm text-blue-600 mt-1">
                {data.impact_delta > 0 ? 'Scenario B reduces impact more' : 'Scenario A is better'}
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-purple-700 mb-2">
                <Users className="w-5 h-5" />
                <span className="font-semibold">Resource Difference</span>
              </div>
              <div className="text-3xl font-bold text-purple-900">
                +{data.resource_delta.officers} Officers
              </div>
              <p className="text-sm text-purple-600 mt-1">
                +{data.resource_delta.barricades} Barricades, +{data.resource_delta.diversions} Diversions
              </p>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-green-700 mb-2">
                <DollarSign className="w-5 h-5" />
                <span className="font-semibold">Cost-Benefit Ratio</span>
              </div>
              <div className="text-3xl font-bold text-green-900">
                {data.cost_benefit_ratio.toFixed(2)}
              </div>
              <p className="text-sm text-green-600 mt-1">
                Impact reduction per additional resource
              </p>
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-900 mb-3">Detailed Comparison</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium text-blue-700 mb-2">Scenario A</div>
                <div className="space-y-1 text-gray-600">
                  <div>Impact Score: {data.scenario_a.impact_score.toFixed(1)}</div>
                  <div>Officers: {data.scenario_a.officer_count}</div>
                  <div>Barricades: {data.scenario_a.barricade_count}</div>
                  <div>Diversions: {data.scenario_a.diversion_count}</div>
                </div>
              </div>
              <div>
                <div className="font-medium text-green-700 mb-2">Scenario B</div>
                <div className="space-y-1 text-gray-600">
                  <div>Impact Score: {data.scenario_b.impact_score.toFixed(1)}</div>
                  <div>Officers: {data.scenario_b.officer_count}</div>
                  <div>Barricades: {data.scenario_b.barricade_count}</div>
                  <div>Diversions: {data.scenario_b.diversion_count}</div>
                </div>
              </div>
            </div>
          </div>

          {data.recommendation && (
            <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="font-semibold text-yellow-900 mb-1">Recommendation</div>
              <p className="text-sm text-yellow-800">{data.recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### `frontend/app/command-center/components/ScenarioConfig.tsx`
```tsx
'use client';

interface SimulationConfig {
  officer_count: number;
  barricade_count: number;
  diversion_count: number;
}

interface ScenarioConfigProps {
  title: string;
  config: SimulationConfig;
  onChange: (config: SimulationConfig) => void;
  color: 'blue' | 'green';
}

export default function ScenarioConfig({ title, config, onChange, color }: ScenarioConfigProps) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-900',
    green: 'bg-green-50 border-green-200 text-green-900'
  };

  const handleChange = (field: keyof SimulationConfig, value: number) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className={`border rounded-lg p-6 ${colorClasses[color]}`}>
      <h3 className="text-lg font-bold mb-4">{title}</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Officers Deployed</label>
          <input
            type="number"
            min="0"
            max="20"
            value={config.officer_count}
            onChange={(e) => handleChange('officer_count', parseInt(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Barricades</label>
          <input
            type="number"
            min="0"
            max="50"
            value={config.barricade_count}
            onChange={(e) => handleChange('barricade_count', parseInt(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Traffic Diversions</label>
          <input
            type="number"
            min="0"
            max="10"
            value={config.diversion_count}
            onChange={(e) => handleChange('diversion_count', parseInt(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
    </div>
  );
}
```

### `frontend/lib/hooks/useSimulationComparison.ts`
```ts
import { useState } from 'react';
import { API_BASE_URL } from '../api';

interface SimulationConfig {
  event_id?: string;
  hypothetical_event?: {
    event_type: string;
    location: { latitude: number; longitude: number };
    start_datetime: string;
  };
  officer_count: number;
  barricade_count: number;
  diversion_count: number;
}

interface SimulationResult {
  impact_score: number;
  officer_count: number;
  barricade_count: number;
  diversion_count: number;
}

interface ComparisonResult {
  scenario_a: SimulationResult;
  scenario_b: SimulationResult;
  impact_delta: number;
  resource_delta: {
    officers: number;
    barricades: number;
    diversions: number;
  };
  cost_benefit_ratio: number;
  recommendation: string;
}

export function useSimulationComparison() {
  const [data, setData] = useState<ComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const compare = async (scenarioA: SimulationConfig, scenarioB: SimulationConfig) => {
    setIsLoading(true);
    setError(null);

    try {
      // Run both simulations in parallel
      const [resultA, resultB] = await Promise.all([
        fetch(`${API_BASE_URL}/api/events/simulate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(scenarioA)
        }).then(res => res.json()),
        fetch(`${API_BASE_URL}/api/events/simulate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(scenarioB)
        }).then(res => res.json())
      ]);

      // Calculate deltas
      const impactDelta = ((resultA.estimated_impact_score - resultB.estimated_impact_score) / resultA.estimated_impact_score) * 100;
      const officerDelta = scenarioB.officer_count - scenarioA.officer_count;
      const barricadeDelta = scenarioB.barricade_count - scenarioA.barricade_count;
      const diversionDelta = scenarioB.diversion_count - scenarioA.diversion_count;
      const totalResourceDelta = officerDelta + barricadeDelta + diversionDelta;
      
      const costBenefitRatio = totalResourceDelta > 0 ? Math.abs(impactDelta) / totalResourceDelta : 0;

      // Generate recommendation
      let recommendation = '';
      if (impactDelta > 5 && costBenefitRatio > 2) {
        recommendation = 'Scenario B provides significantly better impact reduction with good cost-benefit ratio. Recommended for deployment.';
      } else if (impactDelta > 5 && costBenefitRatio < 1) {
        recommendation = 'Scenario B reduces impact but requires substantial additional resources. Consider if resources are available.';
      } else if (Math.abs(impactDelta) < 5) {
        recommendation = 'Both scenarios show similar impact. Scenario A is more resource-efficient.';
      } else {
        recommendation = 'Scenario A provides better resource efficiency for the given situation.';
      }

      setData({
        scenario_a: {
          impact_score: resultA.estimated_impact_score,
          officer_count: scenarioA.officer_count,
          barricade_count: scenarioA.barricade_count,
          diversion_count: scenarioA.diversion_count
        },
        scenario_b: {
          impact_score: resultB.estimated_impact_score,
          officer_count: scenarioB.officer_count,
          barricade_count: scenarioB.barricade_count,
          diversion_count: scenarioB.diversion_count
        },
        impact_delta: impactDelta,
        resource_delta: {
          officers: officerDelta,
          barricades: barricadeDelta,
          diversions: diversionDelta
        },
        cost_benefit_ratio: costBenefitRatio,
        recommendation
      });
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Comparison failed'));
    } finally {
      setIsLoading(false);
    }
  };

  return { data, isLoading, error, compare };
}
```

---

## Database Requirements

- **Database entities affected:** None - uses existing simulation endpoint
- **Migration requirements:** None required.
- **SQL statements:** N/A - frontend-only feature.
- **Indexes:** N/A.
- **Constraints and foreign keys:** N/A.
- **Composite indexes:** N/A.
- **RLS policies:** Not required in MVP.
- **Triggers/stored procedures/functions:** None required.
- **Materialized views:** None required.
- **Rollback migrations:** N/A.
- **Seed data:** Uses existing simulation endpoint from Phase 9.

---

## API Requirements

- **APIs affected:** Reuses existing POST /api/events/simulate endpoint (no changes required)
- **Route definitions:** No new routes needed.
- **Request schemas:** Uses existing SimulationRequest schema.
- **Response schemas:** Uses existing SimulationResponse schema.
- **Validation logic:** Uses existing simulation endpoint validation.
- **Error handling:** Frontend handles comparison failures gracefully.
- **Authentication:** Reuses existing simulation endpoint auth (Level 1/2 access).
- **Authorization:** Same as simulation endpoint authorization.
- **Rate limiting:** Apply existing simulation rate limits (2 scenarios = 2 API calls).
- **Audit logging:** Log comparison requests via existing simulation audit logs.
- **OpenAPI:** No changes required.

---

## Frontend Requirements

- **Frontend scope:** /command-center integration for WhatIfComparison component
- **Pages/components:** Create WhatIfComparison.tsx, ScenarioConfig.tsx components, useSimulationComparison hook.
- **Hooks:** Custom hook for parallel simulation API calls and delta computation.
- **State management:** Local component state for scenario configurations.
- **Forms:** ScenarioConfig component with number inputs for officer/barricade/diversion counts.
- **API integrations:** POST /api/events/simulate (existing endpoint, called twice in parallel).
- **Error states:** Show "Comparison failed" message on API error.
- **Loading states:** Show "Comparing Scenarios..." during parallel API calls.
- **Empty states:** Show empty comparison panel before comparison is run.
- **Permission handling:** Requires Level 1/2 access (admin or registered officer).
- **Routing:** Integrate into existing /command-center page as new comparison panel.

---

## Infrastructure Requirements

- **Dockerfiles:** No changes required.
- **docker-compose:** No changes required.
- **Kubernetes/Terraform:** Not required for MVP.
- **CI/CD:** No changes required.
- **Environment configuration:** No new environment variables required.
- **Secrets configuration:** N/A.
- **Monitoring configuration:** Monitor parallel simulation call performance (target <6s total).
- **Logging configuration:** Reuse existing simulation endpoint logging.
- **Alerting configuration:** Alert if comparison takes longer than 10 seconds.

---

## Security Requirements

- **Authentication model:** Reuses existing simulation endpoint authentication (Level 1/2 only).
- **Authorization model:** Same as simulation endpoint authorization.
- **Threat model:** Protect against excessive parallel simulations, rate limit abuse.
- **Secrets management:** N/A.
- **Audit requirements:** Log comparison requests (2 simulation calls logged separately).
- **Encryption requirements:** HTTPS in deployed environments.
- **Compliance requirements:** No personal data in comparison requests.
- **Security controls:** Rate limiting (applies per simulation call), input validation (via existing endpoint).

---

## Testing Requirements

### Unit Tests

Test useSimulationComparison hook logic for delta calculations and recommendation generation.

### Integration Tests

Test parallel API calls to simulation endpoint with different configurations.

### E2E Tests

Verify WhatIfComparison component renders correctly and displays comparison results.

### Security Tests

Validate rate limiting applies to both simulation calls, authentication required.

### Performance Tests

Verify parallel simulations complete within 6 seconds total.

### Load Tests

Test 10 concurrent comparisons (20 simulation calls total).

### Contract Tests

Ensure frontend uses existing SimulationRequest/Response schemas correctly.

---

## Cross-Phase References & Dependency Tracking

- **Required previous phases:** Phase 9 (simulation engine and POST /api/events/simulate endpoint)
- **Integration method:** Reuses existing simulation API, adds frontend comparison UI.
- **Compatibility requirements:** Do not break existing simulation endpoint contracts.
- **Required interfaces:** POST /api/events/simulate (existing)
- **Required contracts:** SimulationRequest, SimulationResponse schemas (existing).
- **Validation process:** Run two parallel simulations, verify comparison metrics display correctly.

---

## Deliverables

- frontend/app/command-center/components/WhatIfComparison.tsx
- frontend/app/command-center/components/ScenarioConfig.tsx
- frontend/lib/hooks/useSimulationComparison.ts

---

## Technical Design Summary

Build a frontend-only comparison tool that calls the existing simulation endpoint twice in parallel with different resource configurations. Compute impact delta, resource delta, and cost-benefit ratio in the frontend hook. Display side-by-side comparison with visual metrics and recommendation. Zero additional backend engineering required â€” purely frontend orchestration of existing API.

---

## Validation Checklist

### Automated Verification

Run frontend build, E2E tests for comparison component.

### Manual Verification

Test comparison with various officer/barricade/diversion configurations in command center UI.

### Integration Verification

Verify parallel simulation calls complete successfully and results display correctly.

### Security Verification

Check authentication required, rate limiting applies to both calls.

### Performance Verification

Measure total comparison time for parallel simulations (target <6s).

---

## Validation Commands

```bash
npm run build
npm run test
npm run e2e
```

---

## Completion Criteria

Phase is complete only if:

- Comparison component renders correctly in command center.
- Parallel simulations complete within 6 seconds.
- Delta calculations and recommendations display accurately.
- Tests pass.
- Security checks pass (authentication required).
- No paid API dependency is introduced.
- Documentation updated.
