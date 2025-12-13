import sys
import os

# Ensure src is in pythonpath
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crfms.services.database import Database
from crfms.domain.fleet import Location, VehicleClass
from crfms.domain.values import Money
from crfms.persistence.json_io import save_to_json, load_from_json

def main():
    print("1. Creating Data...")
    db = Database()
    
    # Create a location
    loc = Location(name="Test Loc", address="123 Test St")
    db.locations[loc.id] = loc
    
    # Create a class
    vc = VehicleClass(name="Test Class", base_rate=Money(value=50.0))
    db.vehicle_classes[vc.id] = vc
    
    print(f" Created Location: {loc.id}")
    print(f" Created Class: {vc.id}")

    # save
    print("\n2. Saving to 'snapshot.json'...")
    save_to_json(db, "snapshot.json")
    print("   Saved.")

    # load
    print("\n3. Loading from 'snapshot.json'...")
    new_db = load_from_json("snapshot.json")
    
    print(f" Loaded {len(new_db.locations)} locations")
    print(f" Loaded {len(new_db.vehicle_classes)} classes")
    
    # Verify
    loaded_loc = list(new_db.locations.values())[0]
    if loaded_loc.id == loc.id and loaded_loc.name == loc.name:
        print("\nSUCCESS: Data survived the JSON round-trip!")
    else:
        print("\nFAILURE: Data mismatch.")

if __name__ == "__main__":
    main()