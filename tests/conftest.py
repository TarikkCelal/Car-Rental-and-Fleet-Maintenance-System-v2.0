import pytest
from datetime import datetime, timedelta
import uuid

from crfms.domain.values import FixedClock, Money, Kilometers, FuelLevel
from crfms.domain.fleet import Location, VehicleClass, Vehicle, VehicleState
from crfms.domain.users import Customer
from crfms.domain.pricing import PricingPolicy, BaseDailyRateRule
from crfms.services.database import Database
from crfms.services.rental import RentalService
from crfms.services.reservation import ReservationService
from crfms.services.accounting import AccountingService
from crfms.services.maintenance import MaintenanceService
from crfms.services.inventory import InventoryService
from crfms.adapters.notifications import InMemoryNotificationAdapter
from crfms.adapters.payments import FakePaymentAdapter

@pytest.fixture
def clock():
    """ FixedClock set to Nov 1, 2025, 9:00 AM."""
    return FixedClock(datetime(2025, 11, 1, 9, 0, 0))

@pytest.fixture
def db():
    """ Empty the Database."""
    return Database()

@pytest.fixture
def notifier():
    """ InMemoryNotificationAdapter. """
    return InMemoryNotificationAdapter()

@pytest.fixture
def payment_adapter():
    """ FakePaymentAdapter (configured to succeed by default). """
    return FakePaymentAdapter()

@pytest.fixture
def pricing_policy():
    """ PricingPolicy with just the BaseDailyRateRule. """
    return PricingPolicy(rules=[BaseDailyRateRule()])

@pytest.fixture
def rental_service(db, clock, pricing_policy):
    """ A fully configured RentalService."""
    return RentalService(
        db=db,
        clock=clock,
        pricing_policy=pricing_policy,
        daily_mileage_allowance=Kilometers(100),
        mileage_overage_fee_per_km=Money(value=0.5),
        fuel_refill_charge=Money(value=75.0),
        late_fee_per_hour=Money(value=25.0)
    )

@pytest.fixture
def reservation_service(db, clock, notifier):
    """ A fully configured ReservationService."""
    return ReservationService(db, clock, notifier)

@pytest.fixture
def accounting_service(db, payment_adapter, notifier):
    """ A fully configured AccountingService."""
    return AccountingService(db, payment_adapter, notifier)

@pytest.fixture
def maintenance_service(db, clock):
    """ A fully configured MaintenanceService."""
    return MaintenanceService(db, clock)

@pytest.fixture
def inventory_service(db, clock):
    """ A fully configured InventoryService."""
    return InventoryService(db, clock)

# --- Data Fixtures ---
# These fixtures create data in the DB and return the object

@pytest.fixture
def customer(db):
    """ Creates a standard customer and saves to DB. """
    c = Customer(first_name="Jack", last_name="Sparrow", email="jack@mail.com")
    db.customers[c.id] = c
    return c

@pytest.fixture
def location(db):
    """ Creates a standard location and saves to DB. """
    loc = Location(name="Some Place", address="123 Street")
    db.locations[loc.id] = loc
    return loc

@pytest.fixture
def vehicle_class(db):
    """ Creates an 'Economy' vehicle class ($50/day) and saves to DB. """
    vc = VehicleClass(name="Economy", base_rate=Money(value=50.0))
    db.vehicle_classes[vc.id] = vc
    return vc

@pytest.fixture
def vehicle(db, location, vehicle_class):
    """ Creates a standard vehicle (10k km, full tank) and saves to DB. """
    v = Vehicle(
        license_plate="ABC-123",
        odometer=Kilometers(10000),
        fuel_level=FuelLevel(1.0),
        state=VehicleState.AVAILABLE,
        vehicle_class=vehicle_class,
        location=location
    )
    db.vehicles[v.id] = v
    return v