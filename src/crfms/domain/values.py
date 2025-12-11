from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass
from uuid import UUID, uuid4


# Clock

class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime:
        """Returns current time"""
        pass

class SystemClock(Clock):
    """Actual system time."""

    def now(self) -> datetime:

        return datetime.now()

class FixedClock(Clock):
    """Fake clock for testing."""

    def __init__(self, frozen_time: datetime):
        self._frozen_time = frozen_time
    
    def now(self) -> datetime:

        return self._frozen_time



# Measurement Value Objects

@dataclass(frozen=True)
class Kilometers:
    """
    Value Object for distance.
    'frozen=True' so it can't be changed.
    """
    value: int
    
    def __add__(self, other: 'Kilometers') -> 'Kilometers':

        return Kilometers(self.value + other.value)

@dataclass(frozen=True)
class FuelLevel:
    """
    Value Object for fuel level.
    Float number from 0.0 to 1.0
    """
    value: float

@dataclass(frozen=True)
class Money:
    """A Value Object (float) representing money."""
    value: float
    
    def __add__(self, other: 'Money') -> 'Money':

        if not isinstance(other, Money):
            return NotImplemented
            
        return Money(self.value + other.value)

    def __sub__(self, other: 'Money') -> 'Money':
        
        if not isinstance(other, Money):
            return NotImplemented
            
        return Money(self.value - other.value)
    
@dataclass(frozen=True)
class ChargeItem:
    """Value Object for one line item on an invoice. """
    description: str
    amount: Money