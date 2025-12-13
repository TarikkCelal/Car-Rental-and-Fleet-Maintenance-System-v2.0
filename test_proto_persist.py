import sys
import os

# Ensure src is in pythonpath
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crfms.services.database import Database
from crfms.domain.fleet import Location, VehicleClass
from crfms.domain.values import Money
from crfms.persistence.proto_io import save_to_proto, load_from_proto

def main():
    print("1. Creating Data...")
    db = Database()
    
    # Create a location
    loc = Location(name="Binary Branch", address="101010 Binary St")
    db.locations[loc.id] = loc
    
    # Create a class
    vc = VehicleClass(name="ProtoCar", base_rate=Money(value=99.9))
    db.vehicle_classes[vc.id] = vc
    
    print(f" Created Location: {loc.id}")
    print(f" Created Class: {vc.id}")

    # save
    print("\n2. Saving to 'snapshot.bin' (Protocol Buffers)...")
    save_to_proto(db, "snapshot.bin")
    print("   Saved.")

    # load
    print("\n3. Loading from 'snapshot.bin'...")
    new_db = load_from_proto("snapshot.bin")
    
    print(f" Loaded {len(new_db.locations)} locations")
    print(f" Loaded {len(new_db.vehicle_classes)} classes")
    
    # verify
    loaded_loc = list(new_db.locations.values())[0]
    if loaded_loc.id == loc.id and loaded_loc.name == loc.name:
        print("\nSUCCESS: Data survived the Proto round-trip!")
    else:
        print("\nFAILURE: Data mismatch.")

if __name__ == "__main__":
    main()