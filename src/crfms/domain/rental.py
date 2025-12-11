from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from uuid import UUID, uuid4
from typing import List, Optional
from .users import Customer
from .fleet import Vehicle, VehicleClass, Location, AddOn, InsuranceTier
from .values import Money, ChargeItem, Kilometers, FuelLevel
from math import ceil
from .values import Clock, Kilometers
from .pricing import PricingPolicy


# Enums

class ReservationStatus(Enum):
    PENDING = auto()
    CONFIRMED = auto()
    CANCELLED = auto()
    COMPLETED = auto()

class InvoiceStatus(Enum):
    PENDING = auto()
    PAID = auto()
    FAILED = auto()

class BillingPaymentStatus(Enum):
    SUCCESS = auto()
    FAILURE = auto()

# Rental Entities

@dataclass
class Reservation:
    """ customer's reservation entity. """
    customer: Customer
    vehicle_class: VehicleClass
    pickup_location: Location
    return_location: Location
    pickup_time: datetime
    return_time: datetime
    deposit_amount: Money
    id: UUID = field(default_factory=uuid4)
    add_ons: List[AddOn] = field(default_factory=list)
    insurance: Optional[InsuranceTier] = None
    status: ReservationStatus = ReservationStatus.PENDING

@dataclass
class RentalAgreement:
    """ Active rental entity. """
    reservation: Reservation
    vehicle: Vehicle

    pickup_time: datetime
    start_odometer: Kilometers
    start_fuel_level: FuelLevel
    due_time: datetime

    id: UUID = field(default_factory=uuid4)
    return_time: Optional[datetime] = None
    end_odometer: Optional[Kilometers] = None
    end_fuel_level: Optional[FuelLevel] = None

    def extend_due_time(self, new_due_time: datetime, new_deposit: Money):
        """ Updates the due time and deposit for an approved extension. """
        self.due_time = new_due_time
        
    def calculate_final_charges(
        self,
        pricing_policy: PricingPolicy,
        daily_mileage_allowance: Kilometers,
        mileage_overage_fee_per_km: Money,
        fuel_refill_charge: Money,
        late_fee_per_hour: Money
    ) -> List[ChargeItem]:
        """ Calculates all rental charges AND penalties """
        if not all([self.return_time, self.end_odometer, self.end_fuel_level]):

            raise ValueError("Cannot calculate charges before vehicle is returned.")
            
        all_charges: List[ChargeItem] = []
        all_charges.extend(pricing_policy.calculate_total(self))
        
        # Late Fee
        if self.return_time > self.due_time:

            time_late = self.return_time - self.due_time

            if time_late.total_seconds() > 3600:
        
                hours_late = ceil(time_late.total_seconds() / 3600)
                fee = late_fee_per_hour.value * hours_late
                all_charges.append(
                    ChargeItem("Late Return Fee", Money(value=fee))
                )
                
        # Mileage Overage
        rental_days = ceil((self.return_time - self.pickup_time).total_seconds() / 86400)
        allowance_km = daily_mileage_allowance.value * rental_days
        driven_km = self.end_odometer.value - self.start_odometer.value
        
        if driven_km > allowance_km:

            overage_km = driven_km - allowance_km
            fee = mileage_overage_fee_per_km.value * overage_km
            all_charges.append(
                ChargeItem("Mileage Overage Fee", Money(value=fee))
            )
            
        # Fuel Refill
        if self.end_fuel_level.value < self.start_fuel_level.value:

            all_charges.append(
                ChargeItem("Fuel Refill Charge", fuel_refill_charge)
            )
            
        return all_charges


# Billing Entities

@dataclass
class Invoice:
    """
    Entity representing a bill.
    Generates a list of ChargeItems.
    """
    rental_agreement: RentalAgreement
    id: UUID = field(default_factory=uuid4)
    status: InvoiceStatus = InvoiceStatus.PENDING
    charge_items: List[ChargeItem] = field(default_factory=list)
    total_amount: Money = field(default=Money(value=0.0))

    def calculate_total(self):
        """ Sums all chargessto get the final total. """
        total_val = sum(item.amount.value for item in self.charge_items)
        self.total_amount = Money(value=total_val)

@dataclass
class BillingPayment:
    """ Paying invoice entity. """
    invoice: Invoice
    amount_charged: Money
    status: BillingPaymentStatus
    id: UUID = field(default_factory=uuid4)
    transaction_id: Optional[str] = None