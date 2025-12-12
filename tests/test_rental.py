import pytest
from datetime import datetime, timedelta
import uuid

from crfms.domain.values import Money, Kilometers, FuelLevel
from crfms.domain.fleet import VehicleState
from crfms.domain.rental import Reservation, RentalAgreement

def test_idempotent_pickup(db, rental_service, reservation_service, customer, vehicle, clock):
    """
    Verifies that calling pickup_vehicle twice with the same token 
    returns the same agreement and does not duplicate side effects.
    """
    # Setup: Create a reservation
    pickup_time = clock.now()
    due_time = pickup_time + timedelta(days=1)
    
    reservation = reservation_service.create_reservation(
        customer, vehicle.vehicle_class, vehicle.location, vehicle.location,
        pickup_time, due_time, Money(0), [], None
    )
    
    pickup_token = uuid.uuid4().hex
    
    # First Call: Should succeed and create a rental
    agreement1 = rental_service.pickup_vehicle(
        reservation.id, vehicle.id, pickup_token
    )
    
    assert agreement1 is not None
    assert vehicle.state == VehicleState.RENTED
    assert len(db.rental_agreements) == 1
    
    # Second Call: Should return the existing agreement
    agreement2 = rental_service.pickup_vehicle(
        reservation.id, vehicle.id, pickup_token
    )
    
    assert agreement2 == agreement1
    assert agreement2.id == agreement1.id
    assert vehicle.state == VehicleState.RENTED
    assert len(db.rental_agreements) == 1

def test_return_with_charges_and_penalties(db, rental_service, reservation_service, customer, vehicle, clock):
    """
    Verifies charge computation including base rate, late fees, 
    mileage overage, and fuel refill.
    """
    # Rates from conftest: 
    # Base: $50/day (Economy)
    # Late: $25/hour
    # Mileage: 100km/day allowance, $0.50/km overage
    # Fuel: $75 flat
    
    # Pickup
    pickup_time = clock.now()
    due_time = pickup_time + timedelta(days=1) # 1 day rental initially
    
    reservation = reservation_service.create_reservation(
        customer, vehicle.vehicle_class, vehicle.location, vehicle.location,
        pickup_time, due_time, Money(0), [], None
    )
    
    agreement = rental_service.pickup_vehicle(reservation.id, vehicle.id, uuid.uuid4().hex)
    
    # Simulate Conditions for Return
    
    # A. Late Return: 2 hours and 1 minute late
    # Grace period is 1 hour. Time late > 1h implies we charge for the full delay.
    # 2h 1m = ~2.02 hours -> 3 hours charged.
    return_time = due_time + timedelta(hours=2, minutes=1)
    clock._frozen_time = return_time
    
    # B. Mileage Overage
    # Duration: 24h + 2h 1m = 26h 1m.
    # Rental Days calculation: ceil(26h / 24h) = 2 days.
    # Allowance: 2 days * 100km/day = 200 km.
    # Start Odometer: 10,000 (from conftest).
    # We want an overage. Let's drive 250 km. (50km overage).
    end_odo = Kilometers(10250)
    
    # C. Fuel Refill
    # Start: 1.0. End: 0.5.
    end_fuel = FuelLevel(0.5)
    
    #  Return
    invoice = rental_service.return_vehicle(agreement.id, end_odo, end_fuel)
    
    #  Verify Calculations
    
    # Base Charge: 2 days * $50 = $100.0
    # Late Fee: 3 hours * $25 = $75.0 (ceil(2.01 hrs) = 3)
    # Mileage Fee: 50km * $0.50 = $25.0
    # Fuel Charge: $75.0
    # Total Expected: 100 + 75 + 25 + 75 = 275.0
    
    assert invoice.total_amount.value == 275.0
    assert vehicle.state == VehicleState.CLEANING
    assert invoice.status.name == "PENDING"

@pytest.mark.parametrize("has_conflict, expected_success", [
    (False, True),  # No conflict, extension approved
    (True, False)   # Conflict exists, extension denied
])
def test_extension_conflict_logic(
    has_conflict, expected_success,
    db, rental_service, reservation_service, customer, vehicle, clock
):
    """ Verifies that rental extension is denied if a conflicting reservation exists."""
    # Setup Active Rental
    start_time = clock.now()
    original_due = start_time + timedelta(days=1)
    
    res = reservation_service.create_reservation(
        customer, vehicle.vehicle_class, vehicle.location, vehicle.location,
        start_time, original_due, Money(0), [], None
    )
    
    agreement = rental_service.pickup_vehicle(res.id, vehicle.id, uuid.uuid4().hex)
    
    # Setup Conflict Scenario
    # extend to day 4
    new_due_time = original_due + timedelta(days=2)
    
    if has_conflict:
        # Create a reservation that sits in the middle of the extension period
        # Extension: Day 2 -> Day 4
        # Conflict: Day 3 -> Day 3.5
        conflict_start = original_due + timedelta(days=1)
        conflict_end = conflict_start + timedelta(hours=12)
        
        reservation_service.create_reservation(
            customer, vehicle.vehicle_class, vehicle.location, vehicle.location,
            conflict_start, conflict_end, Money(0), [], None
        )
        
    # Attempt Extension
    result = rental_service.extend_rental(agreement.id, new_due_time)
    
    # Assert
    assert result == expected_success

    if expected_success:
        assert agreement.due_time == new_due_time
    else:
        assert agreement.due_time == original_due