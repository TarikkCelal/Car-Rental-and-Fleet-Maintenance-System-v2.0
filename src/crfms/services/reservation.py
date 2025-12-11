from datetime import datetime
from uuid import UUID
from .database import Database
from ..domain.users import Customer
from ..domain.fleet import VehicleClass, Location, AddOn, InsuranceTier
from ..domain.rental import Reservation, ReservationStatus
from ..domain.values import Money, Clock
from ..domain.ports import Notification

class ReservationService:
    """ Service for creating, modifying and canceling reservations. """
    def __init__(self, db: Database, clock: Clock, notifier: Notification):
        self.db = db
        self.clock = clock
        self.notifier = notifier

    def create_reservation(
        self,
        customer: Customer,
        vehicle_class: VehicleClass,
        pickup_loc: Location,
        return_loc: Location,
        pickup_time: datetime,
        return_time: datetime,
        deposit: Money,
        add_ons: list[AddOn],
        insurance: InsuranceTier | None
    ) -> Reservation:
        
        """ Creates a new reservation for a customer."""
        reservation = Reservation(
            customer=customer,
            vehicle_class=vehicle_class,
            pickup_location=pickup_loc,
            return_location=return_loc,
            pickup_time=pickup_time,
            return_time=return_time,
            deposit_amount=deposit,
            add_ons=add_ons,
            insurance=insurance,
            status=ReservationStatus.CONFIRMED
        )
        
        self.db.reservations[reservation.id] = reservation
        
        self.notifier.send(
            customer,
            f"Your reservation {reservation.id} is confirmed."
        )
        return reservation

    def cancel_reservation(self, reservation_id: UUID) -> Reservation:
        """ Cancels an existing reservation. """
        reservation = self.db.reservations[reservation_id]

        if not reservation:
            raise ValueError("Reservation not found.")
            
        reservation.status = ReservationStatus.CANCELLED
        
        self.notifier.send(
            reservation.customer,
            f"Your reservation {reservation.id} has been canceled.")
        return reservation