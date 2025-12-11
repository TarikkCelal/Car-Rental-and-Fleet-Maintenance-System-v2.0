from dataclasses import dataclass, field
from typing import Dict
from uuid import UUID
from ..domain.users import Customer, BranchAgent
from ..domain.fleet import Location, Vehicle, VehicleClass, AddOn, InsuranceTier
from ..domain.rental import Reservation, RentalAgreement, Invoice, BillingPayment

@dataclass
class Database:
    """ It holds all of applications state. """
    customers: Dict[UUID, Customer] = field(default_factory=dict)
    agents: Dict[UUID, BranchAgent] = field(default_factory=dict)
    locations: Dict[UUID, Location] = field(default_factory=dict)
    vehicle_classes: Dict[UUID, VehicleClass] = field(default_factory=dict)
    vehicles: Dict[UUID, Vehicle] = field(default_factory=dict)
    add_ons: Dict[UUID, AddOn] = field(default_factory=dict)
    insurance_tiers: Dict[UUID, InsuranceTier] = field(default_factory=dict)
    reservations: Dict[UUID, Reservation] = field(default_factory=dict)
    rental_agreements: Dict[UUID, RentalAgreement] = field(default_factory=dict)
    invoices: Dict[UUID, Invoice] = field(default_factory=dict)
    payments: Dict[UUID, BillingPayment] = field(default_factory=dict)
    