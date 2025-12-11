from datetime import datetime
from uuid import UUID
from typing import Optional
import uuid
from .database import Database
from ..domain.values import Clock, Kilometers, FuelLevel, Money
from ..domain.fleet import Vehicle, VehicleState
from ..domain.rental import Reservation, RentalAgreement, Invoice, InvoiceStatus
from ..domain.pricing import PricingPolicy

class RentalService:
    """ Rental service for picking up and returning vehicles,extending rentals, and computing charges. """
    def __init__(
        self,
        db: Database,
        clock: Clock,
        pricing_policy: PricingPolicy,

        daily_mileage_allowance: Kilometers,
        mileage_overage_fee_per_km: Money,
        fuel_refill_charge: Money,
        late_fee_per_hour: Money
    ):
        self.db = db
        self.clock = clock
        self.pricing_policy = pricing_policy
        
        self.daily_mileage_allowance = daily_mileage_allowance
        self.mileage_overage_fee_per_km = mileage_overage_fee_per_km
        self.fuel_refill_charge = fuel_refill_charge
        self.late_fee_per_hour = late_fee_per_hour

    def pickup_vehicle(
        self,
        reservation_id: UUID,
        vehicle_id: UUID,
        pickup_token: str
    ) -> RentalAgreement:
        """ Picking up the car, creating a rental agreement. """
        for agreement in self.db.rental_agreements.values():

            if agreement.id.hex == pickup_token:
                return agreement
            
        reservation = self.db.reservations[reservation_id]
        vehicle = self.db.vehicles[vehicle_id]
        
        if not reservation:
            raise ValueError("Reservation not found.")
        
        if not vehicle:
            raise ValueError("Vehicle not found.")


        if vehicle.vehicle_class.id != reservation.vehicle_class.id:
            raise ValueError("Vehicle is not of the reserved class.")
            

        if not vehicle.can_be_assigned(self.clock):
            raise ValueError("Vehicle cannot be assigned (maintenance due or rented).")

        agreement_id = uuid.UUID(hex=pickup_token)
        agreement = RentalAgreement(
            id=agreement_id,
            reservation=reservation,
            vehicle=vehicle,
            pickup_time=self.clock.now(),
            start_odometer=vehicle.odometer,
            start_fuel_level=vehicle.fuel_level,
            due_time=reservation.return_time
        )
        
        vehicle.state = VehicleState.RENTED
        self.db.rental_agreements[agreement.id] = agreement

        return agreement

    def return_vehicle(
        self,
        agreement_id: UUID,
        end_odometer: Kilometers,
        end_fuel_level: FuelLevel
    ) -> Invoice:
        """ Returning car, computing charges and creating an invoice. """
        for inv in self.db.invoices.values():

            if inv.rental_agreement.id == agreement_id:
                return inv
        
        agreement = self.db.rental_agreements[agreement_id]

        if not agreement:
            raise ValueError("Rental agreement not found.")
            
        agreement.return_time = self.clock.now()
        agreement.end_odometer = end_odometer
        agreement.end_fuel_level = end_fuel_level
        
        charges = agreement.calculate_final_charges(
            pricing_policy=self.pricing_policy,
            daily_mileage_allowance=self.daily_mileage_allowance,
            mileage_overage_fee_per_km=self.mileage_overage_fee_per_km,
            fuel_refill_charge=self.fuel_refill_charge,
            late_fee_per_hour=self.late_fee_per_hour
        )
        
        invoice = Invoice(
            rental_agreement=agreement,
            status=InvoiceStatus.PENDING,
            charge_items=charges
        )
        invoice.calculate_total()
        agreement.vehicle.state = VehicleState.CLEANING
        self.db.invoices[invoice.id] = invoice

        return invoice

    def extend_rental(self, agreement_id: UUID, new_due_time: datetime) -> bool:
        """ Extends the rent, checking for conflicts."""
        agreement = self.db.rental_agreements[agreement_id]

        has_conflict = False
        for res in self.db.reservations.values():
            
            if res.pickup_time < new_due_time and \
               res.return_time > agreement.due_time:
                
                has_conflict = True
                break
                
        if has_conflict:
            return False

        agreement.extend_due_time(new_due_time, Money(value=0.0))
        return True