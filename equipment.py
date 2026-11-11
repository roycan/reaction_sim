"""
equipment.py — Abstract Base Class & Subclasses (Inheritance & ABCs)
====================================================================

Models lab equipment: glass containers (beakers, flasks) and digital
sensors (temperature, pH).

OOP CONCEPTS DEMONSTRATED
-------------------------
* Abstract Base Class   — `Equipment` cannot be instantiated; it exists to
                          DEFINE what every piece of equipment must do.
* @abstractmethod       — every concrete subclass MUST implement
                          `inspect_equipment()` or Python refuses to
                          create the object at all.
* Inheritance + super() — subclasses reuse and extend the base __init__,
                          shown here with TWO different init patterns.
* Polymorphism          — one loop over mixed equipment calls each
                          object's OWN inspect_equipment() implementation.

STEM CONCEPTS
-------------
* Preventive maintenance — damaged gear (cracked glass, drifted sensors)
                           is a leading cause of lab accidents.
"""

from abc import ABC, abstractmethod
import random

# Status vocabulary lives in ONE place so no code ever misspells "Ready".
STATUS_READY = "Ready"
STATUS_CRACKED = "Cracked"
STATUS_UNCALIBRATED = "Needs Calibration"


class Equipment(ABC):
    """Abstract base class for every piece of lab equipment."""

    # ------------------------------------------------------------------
    # OOP CONCEPT: Abstract Base Class (ABC & @abstractmethod enforcement)
    # Because this class inherits from ABC and declares an abstractmethod,
    # the line `Equipment("E-000", "Mystery")` raises TypeError at runtime.
    # Python is ENFORCING the contract: you cannot skip the blueprint.
    # ------------------------------------------------------------------
    def __init__(self, item_id: str, name: str, status: str = STATUS_READY) -> None:
        self.item_id = item_id
        self.name = name
        self.status = status

    @abstractmethod
    def inspect_equipment(self) -> str:
        """Return a one-line diagnostic report. MUST be overridden."""
        ...

    def __str__(self) -> str:
        return f"{self.name} [{self.item_id}] — status: {self.status}"


class Glassware(Equipment):
    """A glass container with a working volume (beakers, flasks)."""

    # ------------------------------------------------------------------
    # OOP CONCEPT: Inheritance & super().__init__()
    # PATTERN 1 — the caller supplies the name; we FORWARD it upward so
    # the base class can store the fields every equipment shares.
    # ------------------------------------------------------------------
    def __init__(self, item_id: str, name: str, capacity_ml: int) -> None:
        super().__init__(item_id, name)
        self.capacity_ml = capacity_ml

    def inspect_equipment(self) -> str:
        """Check the glass for cracks (status-based diagnostic)."""
        if self.status == STATUS_CRACKED:
            return (f"✗ [{self.item_id}] {self.name}: CRACKS DETECTED — "
                    f"remove from service and dispose of safely.")
        return (f"✓ [{self.item_id}] {self.name}: glass integrity OK, "
                f"no cracks found (capacity {self.capacity_ml} ml).")


class Sensor(Equipment):
    """A digital measuring device (temperature, pH, ...)."""

    # ------------------------------------------------------------------
    # OOP CONCEPT: Inheritance & super().__init__()
    # PATTERN 2 — the caller never provides a name; we DERIVE one from the
    # sensor type (e.g. "Temperature Sensor"). Both patterns are legitimate
    # designs; each class just has to choose one and stay consistent.
    # ------------------------------------------------------------------
    def __init__(self, item_id: str, sensor_type: str, max_temp_c: float) -> None:
        super().__init__(item_id, name=f"{sensor_type} Sensor")
        self.sensor_type = sensor_type
        self.max_temp_c = max_temp_c

    def inspect_equipment(self) -> str:
        """Verify calibration status."""
        if self.status == STATUS_UNCALIBRATED:
            return (f"✗ [{self.item_id}] {self.name}: OUT OF CALIBRATION — "
                    f"recalibrate before trusting any readings.")
        return (f"✓ [{self.item_id}] {self.name}: calibration verified "
                f"(rated up to {self.max_temp_c:.0f} °C).")

    def take_reading(self, base_temp_c: float) -> float:
        """
        Simulate one sensor measurement near `base_temp_c`.

        STEM CONCEPT: real sensors always carry small measurement noise —
        a reading is never the exact true value of what it measures.
        """
        noisy = base_temp_c + random.uniform(-0.5, 0.5)
        return round(noisy, 1)
