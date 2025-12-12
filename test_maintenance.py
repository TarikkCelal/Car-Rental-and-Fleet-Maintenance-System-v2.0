import pytest
from datetime import timedelta

from crfms.domain.values import Kilometers, FuelLevel
from crfms.domain.fleet import Vehicle, MaintenanceRecord, VehicleState
from crfms.domain.users import Customer

def test_maintenance_due_by_odometer(db, vehicle, clock, maintenance_service):
    """
    Verifies that a vehicle becomes maintenance due when it approaches
    the odometer threshold.
    """

    # Service due every 5,000 km.
    # Current odometer is 10,000 km.
    # So next service should be at 15,000 km.
    # The rule says it becomes due within 500km of the threshold.
    maintenance_service.register_service_plan(
        vehicle=vehicle,
        service_type="Oil Change",
        odometer_threshold=Kilometers(5000), # Interval
        time_threshold=None
    )
    
    record = vehicle.maintenance_records[0]
    record.last_service_odometer = Kilometers(10000)
    record.odometer_threshold = Kilometers(5000) # Next due at 15,000
    
    #  Case A: Not Due Yet (e.g., driven 1000 km -> 11,000 total)
    vehicle.odometer = Kilometers(11000)
    assert vehicle.is_maintenance_due(clock) is False
    assert vehicle.can_be_assigned(clock) is True
    
    # Case B: Entering the "Danger Zone" (within 500km of 15,000)
    # 14,600 km is within 500km of 15,000
    vehicle.odometer = Kilometers(14600)
    assert vehicle.is_maintenance_due(clock) is True
    assert vehicle.can_be_assigned(clock) is False

def test_maintenance_due_by_time(db, vehicle, clock, maintenance_service):
    """ Verifies that a vehicle becomes maintenance-due when the time interval passes."""
    # a time-based plan
    maintenance_service.register_service_plan(
        vehicle=vehicle,
        service_type="Annual Inspection",
        odometer_threshold=None,
        time_threshold=timedelta(days=365)
    )
    
    # 2. Case A: Not Due Yet (1 day later)
    future_clock = clock

    # Set last service to 6 months ago
    record = vehicle.maintenance_records[0]
    record.last_service_date = clock.now() - timedelta(days=180)
    
    assert vehicle.is_maintenance_due(clock) is False
    
    # 3. Case B: Overdue
    # Set last service to 366 days ago
    record.last_service_date = clock.now() - timedelta(days=366)
    
    assert vehicle.is_maintenance_due(clock) is True
    assert vehicle.can_be_assigned(clock) is False

def test_maintenance_service_listing(db, vehicle, location, clock, maintenance_service):
    """ Verifies that the MaintenanceService correctly lists due vehicles. """
    #  Setup: Vehicle is fine initially
    assert len(maintenance_service.list_due_vehicles(location)) == 0
    
    maintenance_service.register_service_plan(
        vehicle=vehicle,
        service_type="Tire Rotation",
        odometer_threshold=Kilometers(1000),
        time_threshold=None
    )
    
    # Last service at 10,000. Interval 1,000. Due at 11,000.
    record = vehicle.maintenance_records[0]
    record.last_service_odometer = Kilometers(10000)
    record.odometer_threshold = Kilometers(1000)
    
    # Drive it to 11,100 (Overdue)
    vehicle.odometer = Kilometers(11100)
    
    # Check list
    due_list = maintenance_service.list_due_vehicles(location)
    assert len(due_list) == 1
    assert due_list[0].license_plate == vehicle.license_plate