from typing import Dict
from .database import Database
from ..domain.values import Clock
from ..domain.fleet import Location, VehicleClass

class InventoryService:
    """ Answers queries about vehicle availability. """
    def __init__(self, db: Database, clock: Clock):
        self.db = db
        self.clock = clock

    def get_availability(self, location: Location) -> Dict[str, Dict]:
        """ Reports which classes are available at a location, """
        report: Dict[str, Dict] = {}

        for vehicle in self.db.vehicles.values():

            if vehicle.location.id != location.id:
                continue

            class_name = vehicle.vehicle_class.name

            if class_name not in report:
                report[class_name] = {"available": 0, "maintenance_hold": 0}

            is_due = vehicle.is_maintenance_due(self.clock)
            
            if is_due:
                report[class_name]["maintenance_hold"] += 1

            elif vehicle.state == vehicle.state.AVAILABLE:
                report[class_name]["available"] += 1
                
        return report