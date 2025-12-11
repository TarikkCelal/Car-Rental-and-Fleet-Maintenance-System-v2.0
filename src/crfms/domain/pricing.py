from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
from datetime import timedelta
from .values import Money, ChargeItem

if TYPE_CHECKING: #to avoid circular imports.
    from .rental import RentalAgreement


# The Strategy Interface

class PricingRule(ABC):
    """ The interface for a single pricing rule. """
    
    @abstractmethod
    def calculate_charges(self, agreement: 'RentalAgreement') -> List[ChargeItem]:
        """ Calculates the charges for this rule based on the agreement."""
        pass


# The Main Pricing Policy

class PricingPolicy:
    """
    This class follows the strategy patern.
    It holds a list of pricing rules and runs them.
    """
    def __init__(self, rules: List[PricingRule]):
        self._rules = rules
    
    def calculate_total(self, agreement: 'RentalAgreement') -> List[ChargeItem]:
        """ Calculates all charges for the rental agreement. """
        all_charges: List[ChargeItem] = []
        for rule in self._rules:
            all_charges.extend(rule.calculate_charges(agreement))
            
        return all_charges


# Concrete Rules

def _get_rental_days(agreement: 'RentalAgreement') -> int:
    """Calculates the duration in days."""
    if agreement.return_time is None:
        return 0
        
    duration = agreement.return_time - agreement.pickup_time
    
    """ Rounds up to the nearest day."""
    days = (duration.total_seconds() / (24 * 3600))
    if days <= 0:
        return 1
    
    int_days = int(days)
    if days > int_days:
        return int_days + 1
    return int_days

class BaseDailyRateRule(PricingRule):
    """ Calculates the base charge for the vehicle class's daily rate. """
    def calculate_charges(self, agreement: 'RentalAgreement') -> List[ChargeItem]:
        days = _get_rental_days(agreement)
        if days == 0:
            return []
        base_rate = agreement.vehicle.vehicle_class.base_rate
        total = base_rate.value * days
        
        return [
            ChargeItem(
                description=f"Base Rate: {agreement.vehicle.vehicle_class.name}",
                amount=Money(value=total)
            )
        ]

class PerDayAddOnRule(PricingRule):
    """ Calculates the charge for all selected daily add-ons."""
    def calculate_charges(self, agreement: 'RentalAgreement') -> List[ChargeItem]:
        days = _get_rental_days(agreement)
        if days == 0 or not agreement.reservation.add_ons:
            return []

        charges: List[ChargeItem] = []
        for add_on in agreement.reservation.add_ons:
            total = add_on.daily_rate.value * days 
            charges.append(
                ChargeItem(
                    description=f"Add-on: {add_on.name}",
                    amount=Money(value=total)
                )
            )
        return charges

class InsuranceRule(PricingRule):
    """ Calculates the charge for the selected insurance tier. """
    def calculate_charges(self, agreement: 'RentalAgreement') -> List[ChargeItem]:
        days = _get_rental_days(agreement)
        insurance = agreement.reservation.insurance
        
        if days == 0 or insurance is None:
            return []
            
        total = insurance.daily_rate.value * days
        return [
            ChargeItem(
                description=f"Insurance: {insurance.name}",
                amount=Money(value=total)
            )
        ]
