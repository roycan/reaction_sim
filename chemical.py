"""
chemical.py — Material Tracking & Expiration (Encapsulation)
=============================================================

Models ONE bottle of chemical reagent in the lab stock room.

WHY THIS FILE COMES FIRST IN THE LESSON SEQUENCE
------------------------------------------------
`Chemical` is the simplest class in the project. It knows NOTHING about
equipment, inventory, or experiments — only about itself: its own data,
and the safe ways other code may interact with that data.

OOP CONCEPTS DEMONSTRATED
-------------------------
* Encapsulation         — attributes and the methods that guard them live
                          together. Outside code must ASK the bottle to
                          pour (use_quantity); it never manipulates
                          volume_ml directly.
* Defensive programming — __init__ validation keeps every object valid
                          from the moment it is born.

STEM CONCEPTS
-------------
* Shelf-life tracking   — reagents degrade; lab safety depends on freshness.
* Hazard classes        — acids, bases, and oxidizers need different storage.
"""

# ---------------------------------------------------------------------------
# Module-level constants use ALL_CAPS names by convention (PEP 8).
# ---------------------------------------------------------------------------

HAZARD_GRADES = ("Acid", "Base", "Oxidizer", "Inert")

# STEM CONCEPT: correct storage is different for every hazard class.
_HANDLING_NOTES = {
    "Acid":     "Corrosive. Wear goggles and gloves. Store BELOW eye level, "
                "separated from bases and oxidizers.",
    "Base":     "Corrosive. Wear goggles and gloves. Store away from acids "
                "and oxidizers.",
    "Oxidizer": "Fire/explosion risk. Keep AWAY from acids, bases, and any "
                "organic material.",
    "Inert":    "Low hazard — but every container still needs a label, a "
                "date, and a shelf-life limit.",
}


class Chemical:
    """A tracked bottle of reagent with a hazard class and shelf life."""

    def __init__(
        self,
        chemical_id: str,
        name: str,
        formula: str,
        volume_ml: float,
        hazard_grade: str,
        shelf_life_days: int,
        days_stored: int = 0,
    ) -> None:
        """
        Create one chemical bottle.

        Args:
            chemical_id:     Unique stock-room ID, e.g. "HCL-001".
            name:            Human-readable name, e.g. "Hydrochloric Acid".
            formula:         Chemical formula, e.g. "HCl".
            volume_ml:       How much liquid the bottle currently holds.
            hazard_grade:    One of HAZARD_GRADES.
            shelf_life_days: Maximum safe storage time in days.
            days_stored:     Days elapsed since the bottle was opened.
        """
        # --- Defensive validation: bad data never becomes an object. ------
        if volume_ml < 0:
            raise ValueError("volume_ml cannot be negative.")
        if hazard_grade not in HAZARD_GRADES:
            raise ValueError(
                f"hazard_grade must be one of {HAZARD_GRADES}, "
                f"got {hazard_grade!r}."
            )
        if shelf_life_days < 0 or days_stored < 0:
            raise ValueError("Shelf-life values cannot be negative.")

        # ------------------------------------------------------------------
        # OOP CONCEPT: Encapsulation — the object owns its data.
        # ------------------------------------------------------------------
        self.chemical_id = chemical_id
        self.name = name
        self.formula = formula
        self.volume_ml = volume_ml
        self.hazard_grade = hazard_grade
        self.shelf_life_days = shelf_life_days
        # DESIGN NOTE: the bottle remembers its OWN age. Callers never keep
        # a side list of "how old is bottle X?" — one owner, one truth.
        self.days_stored = days_stored

    # ------------------------------------------------------------------
    # Shelf-life behaviour
    # ------------------------------------------------------------------

    def is_expired(self) -> bool:
        """Return True once the bottle has passed its shelf life."""
        return self.days_stored > self.shelf_life_days

    # ------------------------------------------------------------------
    # Volume behaviour
    # ------------------------------------------------------------------

    def use_quantity(self, amount_ml: float) -> bool:
        """
        Safely pour `amount_ml` out of the bottle.

        Returns:
            True  — the pour succeeded and the volume was reduced.
            False — rejected (not enough stock, or a non-positive amount).
                    SAFETY GUARANTEE: a rejected pour never changes the
                    volume, and the volume can never drop below 0.
        """
        # Guard 1: pouring 0 ml or a negative amount is a caller bug.
        if amount_ml <= 0:
            return False
        # Guard 2: never dispense more than exists (keeps volume >= 0).
        if amount_ml > self.volume_ml:
            return False
        self.volume_ml -= amount_ml  # guaranteed >= 0 by Guard 2
        return True

    # ------------------------------------------------------------------
    # Safety reporting
    # ------------------------------------------------------------------

    def get_safety_label(self) -> str:
        """Return a formatted GHS-style warning label for this bottle."""
        state = ("⚠ EXPIRED — QUARANTINE FOR DISPOSAL"
                 if self.is_expired() else "✓ Within shelf life")
        return "\n".join([
            f"⚠ SAFETY LABEL — {self.name} ({self.formula})  [{self.chemical_id}]",
            f"   Hazard grade : {self.hazard_grade}",
            f"   Volume       : {self.volume_ml:.1f} ml",
            f"   Shelf life   : {self.shelf_life_days} days "
            f"(stored {self.days_stored})",
            f"   State        : {state}",
            f"   Handling     : {_HANDLING_NOTES[self.hazard_grade]}",
        ])

    def __str__(self) -> str:
        """Readable one-liner, e.g. 'Hydrochloric Acid [HCL-001] — 500.0 ml (Acid)'."""
        return (f"{self.name} [{self.chemical_id}] — "
                f"{self.volume_ml:.1f} ml ({self.hazard_grade})")
