"""
inventory.py — Storage Management (Composition & Aggregation)
=============================================================

Models the lab stock room: every chemical bottle and every piece of
equipment the lab owns, plus a safety log the inventory OWNS outright.

OOP CONCEPTS DEMONSTRATED
-------------------------
* Aggregation            — LabInventory HAS-MANY Chemicals / Equipment,
                           but only by REFERENCE. The objects are built
                           elsewhere, handed in through add_* methods, and
                           keep existing even if the inventory forgets them
                           (hollow diamond o-- in the UML).
* Composition            — LabInventory OWNS its SafetyLog: it is created
                           INSIDE __init__ and lives and dies with the
                           inventory (filled diamond *-- in the UML).
* Dictionary-as-registry — chemical_id -> Chemical lookup in O(1).

STEM CONCEPTS
-------------
* Stock rotation — the shelf-life audit is a real lab chore: expired
                   reagents must be quarantined and disposed of as
                   hazardous waste, never poured down the drain.
"""

from chemical import Chemical
from equipment import Equipment, Glassware, Sensor


class SafetyLog:
    """
    Running record of safety events.

    OOP CONCEPT: Composition — this object is created and owned by
    LabInventory. No outside code holds a reference to it; if the
    inventory object is destroyed, its safety log goes with it.
    """

    def __init__(self) -> None:
        self.entries: list = []

    def add_entry(self, message: str) -> None:
        """Append one timestamped-by-sequence safety record."""
        stamp = f"[entry {len(self.entries) + 1:03d}]"
        self.entries.append(f"{stamp} {message}")

    def show(self) -> str:
        """Return the full log as printable text."""
        if not self.entries:
            return "(safety log is empty — no incidents recorded)"
        return "\n".join(self.entries)


class LabInventory:
    """Central storage manager for one physical lab room."""

    def __init__(self, lab_name: str) -> None:
        self.lab_name = lab_name

        # ------------------------------------------------------------------
        # OOP CONCEPT: Aggregation — HAS-MANY by reference (hollow diamond).
        # The objects are created ELSEWHERE and passed in via add_* methods.
        # The inventory stores REFERENCES, never copies, and does not
        # control their lifecycle.
        # ------------------------------------------------------------------
        self.chemicals: dict = {}      # chemical_id -> Chemical
        self.equipment_list: list = []  # mixed Equipment subclasses!

        # ------------------------------------------------------------------
        # OOP CONCEPT: Composition vs. Aggregation (Storage Containers
        # HAS-A Objects) — this one is TRUE composition: created INSIDE
        # __init__, owned exclusively, dies with the container.
        # ------------------------------------------------------------------
        self.safety_log = SafetyLog()

    # ------------------------------------------------------------------
    # Adding stock (the aggregation entry points)
    # ------------------------------------------------------------------

    def add_chemical(self, chemical: Chemical) -> bool:
        """Register a chemical bottle; rejects duplicate IDs."""
        if chemical.chemical_id in self.chemicals:
            self.safety_log.add_entry(
                f"REJECTED duplicate chemical ID '{chemical.chemical_id}'."
            )
            return False
        self.chemicals[chemical.chemical_id] = chemical
        return True

    def add_equipment(self, equipment: Equipment) -> bool:
        """Register any Equipment subclass; rejects duplicate item IDs."""
        if self.find_equipment(equipment.item_id) is not None:
            self.safety_log.add_entry(
                f"REJECTED duplicate equipment ID '{equipment.item_id}'."
            )
            return False
        self.equipment_list.append(equipment)
        return True

    # ------------------------------------------------------------------
    # Lookup helpers (used by the CLI menu)
    # ------------------------------------------------------------------

    def find_chemical(self, chemical_id: str):
        """Return the Chemical with this ID, or None."""
        return self.chemicals.get(chemical_id)

    def find_equipment(self, item_id: str):
        """Return the Equipment item with this ID, or None."""
        for item in self.equipment_list:
            if item.item_id == item_id:
                return item
        return None

    def glassware_items(self) -> list:
        """Only the Glassware objects (isinstance filters the mixed list)."""
        return [item for item in self.equipment_list
                if isinstance(item, Glassware)]

    def sensors(self) -> list:
        """Only the Sensor objects."""
        return [item for item in self.equipment_list if isinstance(item, Sensor)]

    # ------------------------------------------------------------------
    # STEM CONCEPT: Stock rotation & hazardous-waste disposal
    # ------------------------------------------------------------------

    def audit_shelf_life(self, days_elapsed: int) -> list:
        """
        Advance the lab clock by `days_elapsed` days and flag expired stock.

        This is the ONLY place the clock moves: each bottle's days_stored
        is increased once, then checked against its own shelf life.

        Returns:
            list of expired Chemical objects (may be empty).
        """
        expired = []
        print(f"\n🧪 SHELF-LIFE AUDIT — {self.lab_name} ({days_elapsed} days elapsed)")
        print("-" * 70)
        for chem in self.chemicals.values():
            chem.days_stored += days_elapsed  # the ONE lab clock ticks here
            if chem.is_expired():
                expired.append(chem)
                print(f"  ⚠ EXPIRED: {chem}")
                print("     → quarantine for HAZARDOUS WASTE disposal — do not use!")
                self.safety_log.add_entry(
                    f"EXPIRED stock flagged: {chem.chemical_id} ({chem.name})."
                )
            else:
                remaining = chem.shelf_life_days - chem.days_stored
                print(f"  ✓ OK: {chem} ({remaining} days of shelf life left)")
        if not expired:
            print("  ✅ No expired chemicals found.")
        return expired

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def generate_inventory_report(self) -> None:
        """Print a cleanly aligned table of every chemical and equipment item."""
        print()
        print(f"📋 INVENTORY REPORT — {self.lab_name}")
        print("=" * 78)
        print("CHEMICALS")
        print(f"  {'ID':<10}{'Name':<26}{'Formula':<10}{'Grade':<11}"
              f"{'Volume':>12}  {'Age/Shelf':>10}  State")
        print("-" * 78)
        for chem in self.chemicals.values():
            state = "⚠ EXPIRED" if chem.is_expired() else "✓ OK"
            print(f"  {chem.chemical_id:<10}{chem.name:<26}{chem.formula:<10}"
                  f"{chem.hazard_grade:<11}{chem.volume_ml:>10.1f} ml  "
                  f"{chem.days_stored:>4}/{chem.shelf_life_days:<5}  {state}")
        print()
        print("EQUIPMENT")
        print(f"  {'ID':<10}{'Name':<26}{'Status':<22}Details")
        print("-" * 78)
        for item in self.equipment_list:
            if isinstance(item, Glassware):
                details = f"{item.capacity_ml} ml capacity"
            elif isinstance(item, Sensor):
                details = f"{item.sensor_type} — rated {item.max_temp_c:.0f} °C"
            else:
                details = "-"
            print(f"  {item.item_id:<10}{item.name:<26}{item.status:<22}{details}")
        print("=" * 78)
        print(f"(Safety log entries recorded: {len(self.safety_log.entries)})")
