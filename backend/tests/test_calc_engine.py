import pytest
from app.services.calc_engine import (
    calculate_emissions,
    calculate_scope1_stationary,
    calculate_scope1_mobile,
    calculate_scope1_fugitive,
    calculate_scope2_location,
    calculate_scope2_market,
    calculate_scope3_spend_based,
    convert_quantity
)

def test_unit_conversion():
    # 5 MWh to kWh
    kwh, factor, desc = convert_quantity(5.0, "mwh", "energy")
    assert kwh == 5000.0
    assert factor == 1000.0

    # 100 Gallons to Liters
    liters, factor, desc = convert_quantity(100.0, "gallons", "volume")
    assert round(liters, 2) == 378.54

    # 10 Miles to km
    km, factor, desc = convert_quantity(10.0, "miles", "distance")
    assert round(km, 2) == 16.09

def test_scope1_stationary_combustion():
    # 10,000 Therms of Natural Gas, factor = 0.0053 tCO2e/Therm
    res = calculate_scope1_stationary(
        fuel_quantity=10000.0,
        unit="therms",
        fuel_factor=0.0053,
        factor_denominator="therms",
        uncertainty_pct=5.0,
        allocation_pct=100.0
    )
    assert res["gross_emissions_tco2e"] == 53.0
    assert res["net_emissions_tco2e"] == 53.0
    assert "10000.0 therms" in res["formula_string"]
    assert res["uncertainty_min_tco2e"] == pytest.approx(50.35, 0.01)
    assert res["uncertainty_max_tco2e"] == pytest.approx(55.65, 0.01)

def test_scope1_stationary_with_unit_conversion():
    # 2 MWh converted to kWh factor (0.0002 tCO2e/kWh)
    res = calculate_scope1_stationary(
        fuel_quantity=2.0,
        unit="mwh",
        fuel_factor=0.0002,
        factor_denominator="kwh",
        uncertainty_pct=5.0,
        allocation_pct=80.0
    )
    # 2 MWh = 2000 kWh * 0.0002 = 0.4 tCO2e * 80% = 0.32 tCO2e
    assert pytest.approx(res["gross_emissions_tco2e"], 0.001) == 0.32
    assert "80.0% allocation" in res["formula_string"]

def test_scope1_fugitive():
    # 10 kg R410A leakage, GWP = 2088 kgCO2e/kg -> 2.088 tCO2e/kg
    res = calculate_scope1_fugitive(
        refrigerant_leakage_kg=10.0,
        gwp_factor=2088.0,
        allocation_pct=100.0
    )
    # 10 * 2.088 = 20.88 tCO2e
    assert pytest.approx(res["gross_emissions_tco2e"], 0.01) == 20.88

def test_scope2_location_vs_market():
    # 50,000 kWh electricity
    # Location grid factor = 0.000385 tCO2e/kWh
    loc_res = calculate_scope2_location(50000.0, "kwh", 0.000385, "kwh")
    assert round(loc_res["gross_emissions_tco2e"], 3) == 19.25

    # Market factor with 20 MWh RECs (20,000 kWh) deducted
    mkt_res = calculate_scope2_market(
        electricity_quantity=50000.0,
        unit="kwh",
        supplier_factor=0.000385,
        factor_denominator="kwh",
        recs_mwh=20.0
    )
    # Gross: 19.25, RECs offset: 20 * 1000 * 0.000385 = 7.7
    # Net: 19.25 - 7.7 = 11.55
    assert pytest.approx(mkt_res["gross_emissions_tco2e"], 0.01) == 19.25
    assert pytest.approx(mkt_res["net_emissions_tco2e"], 0.01) == 11.55
    assert "RECs/Offsets" in mkt_res["formula_string"]

def test_scope3_spend_based():
    # $250,000 spend with EEIO factor = 0.00028 tCO2e/USD
    res = calculate_scope3_spend_based(
        spend_usd=250000.0,
        eeio_factor_tco2e_per_usd=0.00028,
        uncertainty_pct=15.0,
        allocation_pct=100.0
    )
    assert res["gross_emissions_tco2e"] == 70.0
    assert res["uncertainty_min_tco2e"] == pytest.approx(59.5, 0.01)
    assert res["uncertainty_max_tco2e"] == pytest.approx(80.5, 0.01)

def test_scope3_freight_unit_conversion():
    from app.services.calc_engine import calculate_scope3_freight
    # 5,000 ton-km with freight factor 0.000105 tCO2e/t-km
    res = calculate_scope3_freight(
        ton_km=5000.0,
        freight_factor=0.000105,
        factor_denominator="t-km",
        unit="t-km"
    )
    assert pytest.approx(res["gross_emissions_tco2e"], 0.0001) == 0.525
    assert "5000.0 t-km" in res["formula_string"]
