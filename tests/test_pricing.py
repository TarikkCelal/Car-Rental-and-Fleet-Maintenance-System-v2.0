import pytest
from datetime import datetime, timedelta
import uuid

from crfms.domain.values import Money, Kilometers, FuelLevel, FixedClock
from crfms.domain.fleet import VehicleClass, Vehicle, Location, VehicleState, AddOn, InsuranceTier
from crfms.domain.users import Customer
from crfms.domain.rental import Reservation, RentalAgreement, ReservationStatus
from crfms.domain.pricing import PricingPolicy, BaseDailyRateRule, PerDayAddOnRule, InsuranceRule

@pytest.mark.parametrize(
    "base_rate_val, duration_days, addons_data, insurance_rate_val, expected_total",
    [
        # Case 1: Simple Economy Rental (3 days @ $50)
        # 50 * 3 = 150
        (50.0, 3, [], None, 150.0),

        # Case 2: SUV Rental (1 day @ $100)
        # 100 * 1 = 100
        (100.0, 1, [], None, 100.0),

        # Case 3: Economy + GPS Add-on (2 days @ $50 base + $10 GPS)
        # (50 * 2) + (10 * 2) = 100 + 20 = 120
        (50.0, 2, [("GPS", 10.0)], None, 120.0),

        # Case 4: Economy + Insurance (2 days @ $50 base + $20 Insurance)
        # (50 * 2) + (20 * 2) = 100 + 40 = 140
        (50.0, 2, [], 20.0, 140.0),

        # Case 5: The "Everything" Rental
        # SUV ($100) + GPS ($10) + BabySeat ($5) + Full Insurance ($30) for 4 days
        # Daily Total: 100 + 10 + 5 + 30 = 145
        # Total: 145 * 4 = 580
        (100.0, 4, [("GPS", 10.0), ("BabySeat", 5.0)], 30.0, 580.0),
    ]
)
def test_pricing_calculation(
    base_rate_val, duration_days, addons_data, insurance_rate_val, expected_total,
    db, customer, location # Fixtures from conftest
):
    " Verifies that the pricing policy correctly sums up base rate, add-ons, and insurance."
    
    # Create Vehicle Class
    vc = VehicleClass(name="TestClass", base_rate=Money(value=base_rate_val))
    
    # Create Add-ons
    add_ons_list = []
    for name, rate in addons_data:
        add_ons_list.append(AddOn(name=name, daily_rate=Money(value=rate)))
        
    # Create Insurance
    insurance = None
    if insurance_rate_val:
        insurance = InsuranceTier(name="TestIns", daily_rate=Money(value=insurance_rate_val))
        
    # Create Vehicle
    vehicle = Vehicle(
        license_plate="PRICE-TEST",
        odometer=Kilometers(1000),
        fuel_level=FuelLevel(1.0),
        vehicle_class=vc,
        location=location
    )
    
    # Setup Rental Agreement
    start_time = datetime(2025, 6, 1, 10, 0)
    end_time = start_time + timedelta(days=duration_days)
    
    reservation = Reservation(
        customer=customer,
        vehicle_class=vc,
        pickup_location=location,
        return_location=location,
        pickup_time=start_time,
        return_time=end_time,
        deposit_amount=Money(value=0),
        add_ons=add_ons_list,
        insurance=insurance,
        status=ReservationStatus.CONFIRMED
    )
    
    agreement = RentalAgreement(
        reservation=reservation,
        vehicle=vehicle,
        pickup_time=start_time,
        start_odometer=vehicle.odometer,
        start_fuel_level=vehicle.fuel_level,
        due_time=end_time,
        return_time=end_time # Simulating it is returned exactly when due
    )
    
    # Configure Pricing Policy
    policy = PricingPolicy(rules=[
        BaseDailyRateRule(),
        PerDayAddOnRule(),
        InsuranceRule()
    ])
    
    charges = policy.calculate_total(agreement)
    
    # Assert
    calculated_total = sum(item.amount.value for item in charges)
    assert calculated_total == expected_total
    expected_items = 1 + len(addons_data) + (1 if insurance else 0)
    assert len(charges) == expected_items