"""Calculation Engine - Pure Functions for Scope 1, 2, 3 Emissions Calculations.

Strict Rules:
- All business/calculation logic resides here (never in UI).
- Auditable formula history string produced for every calculation.
- Unit conversions and uncertainty ranges strictly calculated.
- Pure functions easily testable with pytest.
"""

from typing import Dict, Tuple, Any, Optional

# Standard unit conversion factors to baseline units
# Energy -> kWh
ENERGY_TO_KWH = {
    "kwh": 1.0,
    "mwh": 1000.0,
    "gwh": 1000000.0,
    "therms": 29.3001,
    "therm": 29.3001,
    "mj": 0.277778,
    "gj": 277.778,
    "mmbtu": 293.071,
}

# Liquid volume -> Liters
VOLUME_TO_LITERS = {
    "liters": 1.0,
    "liter": 1.0,
    "l": 1.0,
    "gallons": 3.78541,
    "gallon": 3.78541,
    "gal": 3.78541,
    "m3": 1000.0,
    "barrels": 158.987,
}

# Mass -> Metric Tonnes (t)
MASS_TO_TONNES = {
    "t": 1.0,
    "tonnes": 1.0,
    "metric tonnes": 1.0,
    "mt": 1.0,
    "kg": 0.001,
    "kilograms": 0.001,
    "lbs": 0.000453592,
    "pounds": 0.000453592,
    "g": 0.000001,
}

# Distance -> km
DISTANCE_TO_KM = {
    "km": 1.0,
    "kilometers": 1.0,
    "miles": 1.60934,
    "mile": 1.60934,
    "mi": 1.60934,
}

def normalize_unit(unit: str) -> str:
    return unit.strip().lower()

def convert_quantity(quantity: float, from_unit: str, target_category: str) -> Tuple[float, float, str]:
    """Converts quantity to standard base unit for its category.
    Returns: (converted_quantity, conversion_factor, conversion_description)
    """
    unit_clean = normalize_unit(from_unit)

    if target_category == "energy":
        factor = ENERGY_TO_KWH.get(unit_clean, 1.0)
        return quantity * factor, factor, f"{quantity} {from_unit} * {factor} = {quantity * factor:.4f} kWh"
    
    elif target_category == "volume":
        factor = VOLUME_TO_LITERS.get(unit_clean, 1.0)
        return quantity * factor, factor, f"{quantity} {from_unit} * {factor} = {quantity * factor:.4f} Liters"
    
    elif target_category == "mass":
        factor = MASS_TO_TONNES.get(unit_clean, 1.0)
        return quantity * factor, factor, f"{quantity} {from_unit} * {factor} = {quantity * factor:.6f} t"
    
    elif target_category == "distance":
        factor = DISTANCE_TO_KM.get(unit_clean, 1.0)
        return quantity * factor, factor, f"{quantity} {from_unit} * {factor} = {quantity * factor:.4f} km"
    
    return quantity, 1.0, f"No conversion applied for {from_unit}"

def calculate_emissions(
    quantity: float,
    unit: str,
    factor_value: float,
    factor_denominator: str,
    uncertainty_pct: float = 5.0,
    allocation_pct: float = 100.0,
    recs_or_offsets_tco2e: float = 0.0
) -> Dict[str, Any]:
    """Universal pure calculation function returning audit-grade lineage data.
    
    Args:
        quantity: Raw input activity amount
        unit: Raw activity unit
        factor_value: Emission factor (in tCO2e per base unit)
        factor_denominator: Base unit of the emission factor
        uncertainty_pct: Factor uncertainty percentage (e.g. 5.0 for +/- 5%)
        allocation_pct: Percentage to allocate to this entity/facility (0-100)
        recs_or_offsets_tco2e: Deductions such as EACs/RECs
    """
    unit_clean = normalize_unit(unit)
    denom_clean = normalize_unit(factor_denominator)

    conversion_factor = 1.0
    conversion_desc = "Direct unit match"

    # Determine conversion if unit doesn't match factor denominator directly
    if unit_clean != denom_clean:
        if denom_clean in ENERGY_TO_KWH and unit_clean in ENERGY_TO_KWH:
            conv_kwh, factor_from, _ = convert_quantity(1.0, unit_clean, "energy")
            conv_target, factor_target, _ = convert_quantity(1.0, denom_clean, "energy")
            conversion_factor = factor_from / factor_target
            conversion_desc = f"1 {unit} = {conversion_factor:.4f} {factor_denominator}"
        elif denom_clean in VOLUME_TO_LITERS and unit_clean in VOLUME_TO_LITERS:
            conv_liters, factor_from, _ = convert_quantity(1.0, unit_clean, "volume")
            conv_target, factor_target, _ = convert_quantity(1.0, denom_clean, "volume")
            conversion_factor = factor_from / factor_target
            conversion_desc = f"1 {unit} = {conversion_factor:.4f} {factor_denominator}"
        elif denom_clean in MASS_TO_TONNES and unit_clean in MASS_TO_TONNES:
            conv_mass, factor_from, _ = convert_quantity(1.0, unit_clean, "mass")
            conv_target, factor_target, _ = convert_quantity(1.0, denom_clean, "mass")
            conversion_factor = factor_from / factor_target
            conversion_desc = f"1 {unit} = {conversion_factor:.6f} {factor_denominator}"
        elif denom_clean in DISTANCE_TO_KM and unit_clean in DISTANCE_TO_KM:
            conv_dist, factor_from, _ = convert_quantity(1.0, unit_clean, "distance")
            conv_target, factor_target, _ = convert_quantity(1.0, denom_clean, "distance")
            conversion_factor = factor_from / factor_target
            conversion_desc = f"1 {unit} = {conversion_factor:.4f} {factor_denominator}"

    effective_quantity = quantity * conversion_factor
    allocation_multiplier = max(0.0, min(100.0, allocation_pct)) / 100.0

    gross_emissions = effective_quantity * factor_value * allocation_multiplier
    net_emissions = max(0.0, gross_emissions - recs_or_offsets_tco2e)

    # Uncertainty calculations
    u_pct = max(0.0, uncertainty_pct) / 100.0
    uncertainty_min = gross_emissions * (1.0 - u_pct)
    uncertainty_max = gross_emissions * (1.0 + u_pct)

    # Human-readable auditable formula string
    formula_string = (
        f"({quantity} {unit} * {conversion_factor:.4f} [{conversion_desc}] * "
        f"{factor_value} tCO2e/{factor_denominator}) * {allocation_pct}% allocation = "
        f"{gross_emissions:.6f} tCO2e"
    )
    if recs_or_offsets_tco2e > 0:
        formula_string += f" - {recs_or_offsets_tco2e:.4f} RECs/Offsets = {net_emissions:.6f} tCO2e net"

    return {
        "gross_emissions_tco2e": round(gross_emissions, 6),
        "net_emissions_tco2e": round(net_emissions, 6),
        "rec_offset_tco2e": round(recs_or_offsets_tco2e, 6),
        "uncertainty_min_tco2e": round(uncertainty_min, 6),
        "uncertainty_max_tco2e": round(uncertainty_max, 6),
        "unit_conversion_factor": round(conversion_factor, 6),
        "unit_conversions_applied": conversion_desc,
        "formula_string": formula_string,
        "effective_quantity": round(effective_quantity, 4)
    }

# Dedicated Scope 1 Calculation Wrappers
def calculate_scope1_stationary(
    fuel_quantity: float,
    unit: str,
    fuel_factor: float,
    factor_denominator: str,
    uncertainty_pct: float = 5.0,
    allocation_pct: float = 100.0
) -> Dict[str, Any]:
    return calculate_emissions(fuel_quantity, unit, fuel_factor, factor_denominator, uncertainty_pct, allocation_pct)

def calculate_scope1_mobile(
    distance_or_fuel: float,
    unit: str,
    factor: float,
    factor_denominator: str,
    uncertainty_pct: float = 5.0,
    allocation_pct: float = 100.0
) -> Dict[str, Any]:
    return calculate_emissions(distance_or_fuel, unit, factor, factor_denominator, uncertainty_pct, allocation_pct)

def calculate_scope1_fugitive(
    refrigerant_leakage_kg: float,
    gwp_factor: float, # e.g. R410A GWP = 2088 kgCO2e/kg
    allocation_pct: float = 100.0
) -> Dict[str, Any]:
    # GWP is in kgCO2e/kg -> convert to tCO2e/kg by dividing by 1000
    factor_tco2e = gwp_factor / 1000.0
    return calculate_emissions(refrigerant_leakage_kg, "kg", factor_tco2e, "kg", uncertainty_pct=8.0, allocation_pct=allocation_pct)

# Dedicated Scope 2 Calculation Wrappers (Location vs Market)
def calculate_scope2_location(
    electricity_quantity: float,
    unit: str,
    grid_emission_factor: float,
    factor_denominator: str = "kWh",
    uncertainty_pct: float = 4.0,
    allocation_pct: float = 100.0
) -> Dict[str, Any]:
    return calculate_emissions(electricity_quantity, unit, grid_emission_factor, factor_denominator, uncertainty_pct, allocation_pct)

def calculate_scope2_market(
    electricity_quantity: float,
    unit: str,
    supplier_factor: float,
    factor_denominator: str = "kWh",
    recs_mwh: float = 0.0,
    uncertainty_pct: float = 4.0,
    allocation_pct: float = 100.0
) -> Dict[str, Any]:
    recs_kwh = recs_mwh * 1000.0
    # Deduct RECs emissions: recs_kwh * supplier_factor
    rec_offset_tco2e = (recs_kwh * supplier_factor * (allocation_pct / 100.0))
    return calculate_emissions(
        electricity_quantity,
        unit,
        supplier_factor,
        factor_denominator,
        uncertainty_pct=uncertainty_pct,
        allocation_pct=allocation_pct,
        recs_or_offsets_tco2e=rec_offset_tco2e
    )

# Dedicated Scope 3 Calculations (Categories 1-15)
def calculate_scope3_spend_based(
    spend_usd: float,
    eeio_factor_tco2e_per_usd: float,
    uncertainty_pct: float = 15.0,
    allocation_pct: float = 100.0
) -> Dict[str, Any]:
    return calculate_emissions(spend_usd, "USD", eeio_factor_tco2e_per_usd, "USD", uncertainty_pct, allocation_pct)

def calculate_scope3_freight(
    ton_km: float,
    freight_factor: float,
    factor_denominator: str = "t-km",
    unit: str = "t-km",
    uncertainty_pct: float = 8.0,
    allocation_pct: float = 100.0
) -> Dict[str, Any]:
    return calculate_emissions(ton_km, unit, freight_factor, factor_denominator, uncertainty_pct, allocation_pct)

def calculate_scope3_business_travel(
    passenger_km: float,
    travel_factor: float,
    factor_denominator: str = "p-km",
    unit: str = "p-km",
    uncertainty_pct: float = 10.0,
    allocation_pct: float = 100.0
) -> Dict[str, Any]:
    return calculate_emissions(passenger_km, unit, travel_factor, factor_denominator, uncertainty_pct, allocation_pct)
