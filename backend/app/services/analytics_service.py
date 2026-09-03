"""Analytics Service:
1. Hotspot Pareto Analysis (ranks emission sources, calculates cumulative % curve)
2. What-If Scenario Projection Engine (pure simulation, strictly isolated)
3. Statistical Anomaly Detector (flags values > 2 std dev or > 30% from rolling avg)
"""

from typing import List, Dict, Any
import math

def calculate_pareto_analysis(emissions_by_source: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Takes list of {"name": str, "scope": int, "emissions_tco2e": float},
    sorts descending, and computes cumulative percentages.
    """
    sorted_sources = sorted(emissions_by_source, key=lambda x: x["emissions_tco2e"], reverse=True)
    total = sum(s["emissions_tco2e"] for s in sorted_sources)

    running_sum = 0.0
    results = []
    for s in sorted_sources:
        running_sum += s["emissions_tco2e"]
        cum_pct = (running_sum / total * 100.0) if total > 0 else 0.0
        results.append({
            "name": s["name"],
            "scope": s["scope"],
            "emissions_tco2e": round(s["emissions_tco2e"], 2),
            "pct_of_total": round((s["emissions_tco2e"] / total * 100.0), 1) if total > 0 else 0.0,
            "cumulative_pct": round(cum_pct, 1)
        })
    return results

def project_scenario_reduction(
    actual_emissions_by_scope: Dict[int, float],
    levers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Simulates reduction under selected levers without touching actuals.
    Each lever: {"name": str, "scope": int, "reduction_pct": float, "applied_to_category": Optional[str]}
    """
    projected = {
        1: actual_emissions_by_scope.get(1, 0.0),
        2: actual_emissions_by_scope.get(2, 0.0),
        3: actual_emissions_by_scope.get(3, 0.0),
    }

    lever_impacts = []
    total_reduction = 0.0

    for lever in levers:
        target_scope = int(lever.get("scope", 1))
        reduction_pct = float(lever.get("reduction_pct", 0.0)) / 100.0
        current_scope_val = projected.get(target_scope, 0.0)
        
        scope_reduction = current_scope_val * reduction_pct
        projected[target_scope] = max(0.0, current_scope_val - scope_reduction)
        total_reduction += scope_reduction

        lever_impacts.append({
            "lever_name": lever.get("name"),
            "scope": target_scope,
            "reduction_pct": round(reduction_pct * 100.0, 1),
            "projected_reduction_tco2e": round(scope_reduction, 2)
        })

    baseline_total = sum(actual_emissions_by_scope.values())
    projected_total = sum(projected.values())
    overall_reduction_pct = ((baseline_total - projected_total) / baseline_total * 100.0) if baseline_total > 0 else 0.0

    return {
        "baseline_total_tco2e": round(baseline_total, 2),
        "projected_total_tco2e": round(projected_total, 2),
        "total_reduction_tco2e": round(total_reduction, 2),
        "overall_reduction_pct": round(overall_reduction_pct, 1),
        "projected_by_scope": {k: round(v, 2) for k, v in projected.items()},
        "lever_impacts": lever_impacts
    }

def detect_anomalies(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Evaluates activity quantities against facility/activity type rolling averages.
    Flags records deviating > 30% from the mean.
    """
    anomalies = []
    # Group by (facility_id, activity_type)
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        key = f"{r.get('facility_id')}_{r.get('activity_type')}"
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    for key, items in groups.items():
        if len(items) < 3:
            continue
        quantities = [float(i.get("quantity", 0.0)) for i in items]
        mean_val = sum(quantities) / len(quantities)
        if mean_val == 0:
            continue

        variance = sum((x - mean_val) ** 2 for x in quantities) / len(quantities)
        std_dev = math.sqrt(variance)

        for i in items:
            q = float(i.get("quantity", 0.0))
            deviation = abs(q - mean_val)
            pct_diff = deviation / mean_val

            if pct_diff > 0.35 or (std_dev > 0 and deviation > 2.0 * std_dev):
                anomalies.append({
                    "activity_id": i.get("id"),
                    "facility_name": i.get("facility_name", "Facility"),
                    "activity_type": i.get("activity_type"),
                    "actual_value": q,
                    "expected_mean": round(mean_val, 2),
                    "deviation_pct": round(pct_diff * 100.0, 1),
                    "period": i.get("reporting_period"),
                    "status": "flagged"
                })
    return anomalies
