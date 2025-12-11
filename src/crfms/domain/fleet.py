from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from uuid import UUID, uuid4
from .values import Kilometers, FuelLevel, Money
from typing import List, Optional
from math import ceil
from .values import Clock

# Enum

class VehicleState(Enum):
    """ Availability states for a vehicle. """
    AVAILABLE = auto()
    RESERVED = auto()
    RENTED = auto()
    OUT_OF_SERVICE = auto()
    CLEANING = auto()


# Entities

@dataclass
class Location:
    """ Rental branch entity. """
    name: str
    address: str
    id: UUID = field(default_factory=uuid4)

@dataclass
class VehicleClass:
    """ Vehicle class entity. """
    name: str
    base_rate: Money
    id: UUID = field(default_factory=uuid4)

@dataclass
class AddOn:
    """ Add-on entity."""
    name: str
    daily_rate: Money
    id: UUID = field(default_factory=uuid4)

@dataclass
class InsuranceTier:
    """ Insurance tier entity. """
    name: str
    daily_rate: Money
    id: UUID = field(default_factory=uuid4)

@dataclass
class Vehicle:
    """ Concrete vehicle. """
    license_plate: str
    odometer: Kilometers
    fuel_level: FuelLevel
    vehicle_class: VehicleClass
    location: Location
    id: UUID = field(default_factory=uuid4)
    state: VehicleState = VehicleState.AVAILABLE
    maintenance_records: List['MaintenanceRecord'] = field(default_factory=list)

    def is_maintenance_due(self, clock: Clock) -> bool:
        """ Checks if any maintenance record for this vehicle is due."""
        for record in self.maintenance_records:
            if record.is_due(self, clock):
                return True
        return False
        
    def can_be_assigned(self, clock: Clock) -> bool:
        """ Checks if the vehicle is available to rent."""
        if self.state != VehicleState.AVAILABLE:
            return False
            
        if self.is_maintenance_due(clock):
            return False
            
        return True

@dataclass
class MaintenanceRecord:
    """Maintenance record entity."""
    vehicle: Vehicle
    service_type: str 
    id: UUID = field(default_factory=uuid4)
    odometer_threshold: Kilometers | None = None
    time_threshold: timedelta | None = None
    last_service_date: datetime | None = None
    last_service_odometer: Kilometers | None = None

    def is_due(self, vehicle: Vehicle, clock: Clock) -> bool:
        """Checks if this maintenance is due for the given vehicle."""
        current_time = clock.now()
        
        if self.odometer_threshold and self.last_service_odometer:

            km_since_service = vehicle.odometer.value - self.last_service_odometer.value
            km_until_due = self.odometer_threshold.value - km_since_service
            
            if km_until_due <= 500:
                return True
                
        if self.time_threshold and self.last_service_date:

            time_since_service = current_time - self.last_service_date

            if time_since_service >= self.time_threshold:
                return True
                
        return False