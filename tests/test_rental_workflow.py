import pytest
from datetime import datetime, timedelta
import uuid
from crfms.domain.values import (FixedClock, Money, Kilometers, FuelLevel)
from crfms.domain.fleet import (Location, VehicleClass, Vehicle, VehicleState)
from crfms.domain.users import Customer, BranchAgent
from crfms.domain.pricing import (PricingPolicy, BaseDailyRateRule)
from crfms.domain.rental import (InvoiceStatus, BillingPaymentStatus, Reservation, RentalAgreement, Invoice)
from crfms.services.database import Database
from crfms.services.reservation import ReservationService
from crfms.services.rental import RentalService
from crfms.services.accounting import AccountingService
from crfms.adapters.notifications import InMemoryNotificationAdapter
from crfms.adapters.payments import FakePaymentAdapter


@pytest.fixture
def setup():
    """ Set up a clean database, clock, and all services for each test. """
    
    # Nov 1 2025 - 9:00 AM
    start_time = datetime(2025, 11, 1, 9, 0, 0)
    clock = FixedClock(start_time)
    
    db = Database()
    notifier = InMemoryNotificationAdapter()
    payment_adapter = FakePaymentAdapter()
    policy = PricingPolicy(rules=[BaseDailyRateRule()])
    
    reservation_service = ReservationService(db, clock, notifier)
    rental_service = RentalService(
        db=db,
        clock=clock,
        pricing_policy=policy,
        daily_mileage_allowance=Kilometers(100),
        mileage_overage_fee_per_km=Money(value=0.5),
        fuel_refill_charge=Money(value=75.0),
        late_fee_per_hour=Money(value=25.0)
    )
    accounting_service = AccountingService(db, payment_adapter, notifier)
    
    customer = Customer(first_name="Test", last_name="User", email="test@gmail.com")
    db.customers[customer.id] = customer
    
    location = Location(name="Test Branch", address="123 Street 321 Apartment")
    db.locations[location.id] = location
    
    v_class = VehicleClass(name="Economy", base_rate=Money(value=50.0))
    db.vehicle_classes[v_class.id] = v_class
    
    vehicle = Vehicle(
        license_plate="34-AAA",
        odometer=Kilometers(10000),
        fuel_level=FuelLevel(1.0),
        state=VehicleState.AVAILABLE,
        vehicle_class=v_class,
        location=location
    )
    db.vehicles[vehicle.id] = vehicle
    
    return (
        db, clock, reservation_service, rental_service,
        accounting_service, notifier, payment_adapter,
        customer, vehicle
    )



# TESTS

def test_full_rental_workflow(setup):
    """ 1- Tests the successfull path: create reservation, pickup, return, and pay. """
    # 1. Get all setup components
    (
        db, clock, res_service, rental_service,
        acct_service, notifier, payment_adapter,
        customer, vehicle
    ) = setup

    # 2. Create Reservation
    pickup_time = datetime(2025, 11, 2, 9, 0) # Nov 2
    return_time = datetime(2025, 11, 5, 9, 0) # Nov 5
    
    reservation = res_service.create_reservation(
        customer=customer,
        vehicle_class=vehicle.vehicle_class,
        pickup_loc=vehicle.location,
        return_loc=vehicle.location,
        pickup_time=pickup_time,
        return_time=return_time,
        deposit=Money(value=100.0),
        add_ons=[],
        insurance=None
    )
    
    # 3. Pickup Vehicle
    clock._frozen_time = pickup_time
    
    agreement = rental_service.pickup_vehicle(
        reservation_id=reservation.id,
        vehicle_id=vehicle.id,
        pickup_token=uuid.uuid4().hex
    )
    assert vehicle.state == VehicleState.RENTED
    assert agreement.start_odometer.value == 10000

    # 4. Return Vehicle
    clock._frozen_time = return_time
    
    # we drove 350km (50 overage) and tank is half full
    end_odo = Kilometers(10350)
    end_fuel = FuelLevel(0.5)
    
    invoice = rental_service.return_vehicle(
        agreement_id=agreement.id,
        end_odometer=end_odo,
        end_fuel_level=end_fuel
    )
    
    # 3 days @ 50$/day = 150$
    # 50km overage @ 0.5/km = 25$
    # Fuel refill charge = 75$
    # Total = 250$
    assert invoice.total_amount.value == 250.0
    assert len(invoice.charge_items) == 3
    assert vehicle.state == VehicleState.CLEANING

    # 5. Final Payment
    payment_adapter.should_succeed = True
    acct_service.finalize_payment(invoice)
    
    assert invoice.status == InvoiceStatus.PAID
    assert len(notifier.sent_messages) == 2
    assert "successful" in notifier.sent_messages[-1][1]


def test_payment_failure(setup):
    """ Tests if a failed payment is handled correctly. """
    # 1. Get components
    (
        db, clock, res_service, rental_service,
        acct_service, notifier, payment_adapter,
        customer, vehicle
    ) = setup
    
    # 2. Create a "fake" invoice
    invoice = Invoice(
        rental_agreement=RentalAgreement(
            reservation=Reservation(customer=customer, vehicle_class=vehicle.vehicle_class, 
                pickup_location=vehicle.location, return_location=vehicle.location,
                pickup_time=clock.now(), return_time=clock.now(), deposit_amount=Money(0.0)),
            vehicle=vehicle,
            pickup_time=clock.now(),
            start_odometer=vehicle.odometer,
            start_fuel_level=vehicle.fuel_level,
            due_time=clock.now()
        ),
        total_amount=Money(value=100.0)
    )

    # 3. Tell the adapter to FAIL
    payment_adapter.should_succeed = False
    
    # 4. Final Payment
    acct_service.finalize_payment(invoice)
    
    # 5. Check the result
    assert invoice.status == InvoiceStatus.FAILED
    assert len(db.payments.values()) == 1
    
    payment_record = list(db.payments.values())[0]
    assert payment_record.status == BillingPaymentStatus.FAILURE
    
    assert len(notifier.sent_messages) == 1
    assert "Payment failed" in notifier.sent_messages[0][1]