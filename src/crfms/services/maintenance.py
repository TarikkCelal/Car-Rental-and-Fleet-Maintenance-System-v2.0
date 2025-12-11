from typing import List
from datetime import datetime, timedelta
from .database import Database
from ..domain.values import Clock, Kilometers
from ..domain.fleet import Vehicle, Location, MaintenanceRecord

class MaintenanceService:
    """ Fleet maintenance service. """
    def __init__(self, db: Database, clock: Clock):
        self.db = db
        self.clock = clock
        
    def register_service_plan(
        self,
        vehicle: Vehicle,
        service_type: str,
        odometer_threshold: Kilometers,
        time_threshold: timedelta,
    ):
        """ Registers a new maintenance plan for a vehicle. """
        record = MaintenanceRecord(
            vehicle=vehicle,
            service_type=service_type,
            odometer_threshold=odometer_threshold,
            time_threshold=time_threshold,
            last_service_date=self.clock.now(),
            last_service_odometer=vehicle.odometer
        )
        vehicle.maintenance_records.append(record)
        
    def list_due_vehicles(self, location: Location) -> List[Vehicle]:
        """ Lists all vehicles at a location that are due for maintenance. """
        due_vehicles: List[Vehicle] = []
        
        for vehicle in self.db.vehicles.values():

            if vehicle.location.id != location.id:
                continue
                
            if vehicle.is_maintenance_due(self.clock):
                due_vehicles.append(vehicle)
                
        return due_vehicles