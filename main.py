"""
main.py — Interactive CLI Driver Loop
=====================================

The "front desk" of the Digital Science Lab. It owns the LabInventory,
lends objects INTO the Experiment (dependency injection), and turns every
safety rejection into a readable message instead of a crash.

Run with:  python main.py
"""

from typing import Optional

from chemical import Chemical, HAZARD_GRADES
from equipment import (
    Glassware,
    Sensor,
    STATUS_CRACKED,
    STATUS_READY,
    STATUS_UNCALIBRATED,
)
from experiment import Experiment, SafetyViolationError
from inventory import LabInventory

# ---------------------------------------------------------------------------
# PEDAGOGICAL ANNOTATION 1 — ASCII UML CLASS DIAGRAM
#   --|>  inheritance (IS-A, hollow triangle)
#   o--   aggregation  (HAS-MANY by reference, hollow diamond)
#   *--   composition  (OWNS-A, created internally, filled diamond)
#   ..>   dependency   (USES-A, passed in as parameters, dashed arrow)
# ---------------------------------------------------------------------------
UML_CLASS_MAP = """\
+==========================================================================+
|                 DIGITAL SCIENCE LAB  --  UML CLASS MAP                   |
+==========================================================================+
|  INHERITANCE -- IS-A (hollow-triangle arrows)                            |
|    Glassware   --|>  Equipment                                           |
|    Sensor      --|>  Equipment                                           |
|    Equipment {abstract}: @abstractmethod inspect_equipment()             |
|                                                                          |
|  AGGREGATION -- HAS-MANY by reference (hollow diamond o--)               |
|    LabInventory  o--  Chemical     (dict keyed by chemical_id)           |
|    LabInventory  o--  Equipment    (list holding mixed subclasses)       |
|                                                                          |
|  COMPOSITION -- OWNS-A, created internally (filled diamond *--)          |
|    LabInventory  *--  SafetyLog    (built inside LabInventory.__init__)  |
|                                                                          |
|  DEPENDENCY -- USES-A, passed in as parameters (dashed arrow ..>)        |
|    Experiment  ..>  Chemical      (borrowed during run_reaction)         |
|    Experiment  ..>  Equipment     (borrowed during run_reaction)         |
+==========================================================================+
"""

MENU = """\
+----------------------------------------------------------------------+
|                      LAB MANAGER MAIN MENU                           |
+----------------------------------------------------------------------+
|  1) View Complete Lab Inventory & Equipment Status                   |
|  2) Conduct Chemical Reaction Experiment                             |
|  3) Run Chemical Shelf-Life Audit (advances the clock by 30 days)    |
|  4) Inspect Lab Equipment Integrity                                  |
|  5) Add New Chemical / Equipment to Stock                            |
|  6) Assemble an Experiment Kit (certify vessel + sensor)             |
|  7) Exit                                                             |
+----------------------------------------------------------------------+"""


# ---------------------------------------------------------------------------
# Small, reusable input helpers — every user answer is validated in a loop,
# so bad typing can never crash the program.
# ---------------------------------------------------------------------------

def _ask_float(prompt: str, minimum: float, default: Optional[float] = None) -> float:
    """Keep asking until the user types a valid float >= minimum."""
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        try:
            value = float(raw)
        except ValueError:
            print("   Please type a number, e.g. 25 or 25.5")
            continue
        if value < minimum:
            print(f"   Value must be at least {minimum}.")
            continue
        return value


def _ask_int(prompt: str, minimum: int,
             maximum: Optional[int] = None,
             default: Optional[int] = None) -> int:
    """Keep asking until the user types a valid whole number in range."""
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        if not raw.isdigit():  # also rejects negatives — fine for this lab
            print("   Please type a whole number.")
            continue
        value = int(raw)
        if value < minimum or (maximum is not None and value > maximum):
            if maximum is not None:
                print(f"   Enter a number from {minimum} to {maximum}.")
            else:
                print(f"   Enter a number of at least {minimum}.")
            continue
        return value


def _ask_text(prompt: str) -> str:
    """Return stripped user text (callers treat empty as 'cancel')."""
    return input(prompt).strip()


# ---------------------------------------------------------------------------
# Selection helpers for the menus
# ---------------------------------------------------------------------------

def _pick_chemical(lab: LabInventory, slot: str) -> Optional[Chemical]:
    """Ask for a chemical ID until it matches stock ('q' cancels)."""
    chem_id = _ask_text(f"   Type the {slot} bottle ID (or 'q' to cancel): ")
    if chem_id.lower() == "q":
        print("   Cancelled.")
        return None
    chem = lab.find_chemical(chem_id)
    if chem is None:
        print(f"   🚫 Unknown chemical ID '{chem_id}'.")
        return None
    return chem


def _pick_equipment(items: list, label: str):
    """Show a numbered list of equipment and return the chosen item."""
    if not items:
        print(f"   🚫 No {label} available in stock.")
        return None
    print(f"   Select a {label}:")
    for idx, item in enumerate(items, start=1):
        print(f"     {idx}) {item}")
    pick = _ask_int(f"   Number 1-{len(items)}: ", minimum=1, maximum=len(items))
    return items[pick - 1]


# ---------------------------------------------------------------------------
# Default setup — the seed data deliberately exercises EVERY feature.
# ---------------------------------------------------------------------------

def build_default_lab() -> LabInventory:
    """Populate the starter inventory used by the interactive menu."""
    lab = LabInventory("Grade 9 Science Lab")

    # -- Aggregation seeds: objects built HERE, then HANDED to the lab. ---
    seed_chemicals = [
        Chemical("HCL-001", "Hydrochloric Acid", "HCl", 500.0, "Acid", 900, 120),
        Chemical("NAOH-001", "Sodium Hydroxide", "NaOH", 500.0, "Base", 730, 80),
        Chemical("H2O-001", "Distilled Water", "H2O", 1000.0, "Inert", 9999, 10),
        # DEMO SEED: opened 400 days ago on a 180-day shelf → ALREADY EXPIRED.
        Chemical("H2O2-001", "Hydrogen Peroxide", "H2O2", 300.0, "Oxidizer", 180, 400),
    ]
    for chem in seed_chemicals:
        lab.add_chemical(chem)

    seed_equipment: list = [
        Glassware("GLS-001", "Beaker", 250),
        Sensor("SEN-001", "Temperature", 120.0),
    ]
    # DEMO SEED: pre-cracked vessel — run_reaction() must refuse it.
    cracked_flask = Glassware("GLS-002", "Erlenmeyer Flask", 100)
    cracked_flask.status = STATUS_CRACKED
    seed_equipment.append(cracked_flask)
    # DEMO SEED: skipped calibration day — run_reaction() must refuse it.
    ph_sensor = Sensor("SEN-002", "pH", 60.0)
    ph_sensor.status = STATUS_UNCALIBRATED
    seed_equipment.append(ph_sensor)
    for item in seed_equipment:
        lab.add_equipment(item)

    return lab


# ---------------------------------------------------------------------------
# Menu option handlers
# ---------------------------------------------------------------------------

def conduct_experiment_menu(lab: LabInventory, experiment: Experiment) -> None:
    """Menu 2 — gather four objects, then inject them into run_reaction()."""
    print(f"\n⚗️  CONDUCT EXPERIMENT — {experiment.title}")
    print(f"   Required hazard clearance: {experiment.required_hazard_clearance}")
    print("\n   Available reagents:")
    for chem in lab.chemicals.values():
        print(f"     {chem}")

    chem1 = _pick_chemical(lab, "FIRST")
    if chem1 is None:
        return
    chem2 = _pick_chemical(lab, "SECOND")
    if chem2 is None:
        return
    if chem2 is chem1:
        print("   🚫 Pick two DIFFERENT bottles.")
        return

    vessel = _pick_equipment(lab.glassware_items(), "reaction vessel")
    if vessel is None:
        return
    sensor = _pick_equipment(lab.sensors(), "monitoring sensor")
    if sensor is None:
        return

    dose_ml = _ask_float(
        "   Ml to dispense from EACH bottle [Enter = 25.0]: ",
        minimum=1.0, default=25.0,
    )

    # ------------------------------------------------------------------
    # OOP CONCEPT: Dependency Injection — the menu hands the SHARED lab
    # objects INTO the experiment. The Experiment owns none of them; it
    # only borrows them for this single method call.
    # ------------------------------------------------------------------
    try:
        print(experiment.run_reaction(chem1, chem2, vessel, sensor, dose_ml=dose_ml))
    except SafetyViolationError as err:
        print("\n🚫 SAFETY ABORT — reaction blocked, no stock consumed.")
        print(f"   Reason: {err}")
        lab.safety_log.add_entry(f"Reaction '{experiment.title}' blocked: {err}")


def inspect_equipment_menu(lab: LabInventory) -> None:
    """Menu 4 — one polymorphic loop over mixed equipment subclasses."""
    print(f"\n🔧 EQUIPMENT INTEGRITY CHECK — {len(lab.equipment_list)} items")
    print("-" * 70)
    # ------------------------------------------------------------------
    # OOP CONCEPT: Polymorphism payoff — ONE loop over MIXED subclasses.
    # Python picks each object's OWN inspect_equipment() at runtime:
    # Glassware reports cracks, Sensor reports calibration. This only
    # works because the ABC guarantees the method exists on every item.
    # ------------------------------------------------------------------
    for item in lab.equipment_list:
        print(f"  {item.inspect_equipment()}")


def _add_chemical(lab: LabInventory) -> None:
    """Interactive form for a new chemical bottle."""
    print("\n➕ ADD CHEMICAL BOTTLE  (leave ID empty to cancel)")
    chemical_id = _ask_text("   Stock ID (e.g. NACL-001): ")
    if not chemical_id:
        return
    if lab.find_chemical(chemical_id) is not None:
        print(f"   🚫 ID '{chemical_id}' already exists.")
        return
    name = _ask_text("   Name (e.g. Salt Solution): ")
    if not name:
        return
    formula = _ask_text("   Formula (e.g. NaCl): ") or "—"
    volume_ml = _ask_float("   Starting volume (ml): ", minimum=0.1)
    print("   Hazard grade options:")
    for idx, grade in enumerate(HAZARD_GRADES, start=1):
        print(f"     {idx}) {grade}")
    pick = _ask_int("   Choose 1-4: ", minimum=1, maximum=len(HAZARD_GRADES))
    hazard_grade = HAZARD_GRADES[pick - 1]
    shelf_life_days = _ask_int("   Shelf life (days): ", minimum=1)
    days_stored = _ask_int("   Days already stored [Enter = 0]: ",
                           minimum=0, default=0)
    try:
        chemical = Chemical(chemical_id, name, formula, volume_ml,
                            hazard_grade, shelf_life_days, days_stored)
    except ValueError as err:
        print(f"   🚫 Invalid data: {err}")
        return
    if lab.add_chemical(chemical):
        print(f"   ✅ Added {chemical}")
    else:
        print("   🚫 Could not register that chemical.")


def _add_equipment(lab: LabInventory) -> None:
    """Interactive form for new glassware or a new sensor."""
    print("\n➕ ADD EQUIPMENT  (1) Glassware  (2) Sensor")
    kind = _ask_text("   Choose 1-2: ")
    if kind == "1":
        item_id = _ask_text("   Item ID (e.g. GLS-003): ")
        if not item_id:
            return
        name = _ask_text("   Name (e.g. Round-bottom Flask): ")
        if not name:
            return
        capacity_ml = _ask_int("   Capacity (ml): ", minimum=1)
        item = Glassware(item_id, name, capacity_ml)
    elif kind == "2":
        item_id = _ask_text("   Item ID (e.g. SEN-003): ")
        if not item_id:
            return
        sensor_type = _ask_text("   Sensor type (e.g. Thermocouple): ")
        if not sensor_type:
            return
        max_temp_c = _ask_float("   Max rated temperature (°C): ", minimum=1.0)
        item = Sensor(item_id, sensor_type, max_temp_c)
    else:
        print("   Cancelled.")
        return
    if lab.add_equipment(item):
        print(f"   ✅ Added {item}")
    else:
        print(f"   🚫 Equipment ID '{item.item_id}' already exists.")


def add_stock_menu(lab: LabInventory) -> None:
    """Menu 5 — sub-menu choosing which kind of stock to add."""
    print("\n   1) Add a chemical bottle")
    print("   2) Add equipment")
    choice = _ask_text("   Choose 1-2: ")
    if choice == "1":
        _add_chemical(lab)
    elif choice == "2":
        _add_equipment(lab)
    else:
        print("   Cancelled.")


def assemble_kit_menu(lab: LabInventory) -> None:
    """Menu 6 — certify a vessel + sensor pair before an experiment."""
    print("\n🎒 ASSEMBLE AN EXPERIMENT KIT")
    vessel = _pick_equipment(lab.glassware_items(), "vessel")
    if vessel is None:
        return
    sensor = _pick_equipment(lab.sensors(), "sensor")
    if sensor is None:
        return

    # ------------------------------------------------------------------
    # OOP CONCEPT: the abstract contract at work. Because `Equipment`
    # GUARANTEES inspect_equipment() on every subclass, this code can ask
    # any object for its own diagnostic without knowing its concrete type
    # — that is the real reason the ABC exists.
    # ------------------------------------------------------------------
    print(f"   {vessel.inspect_equipment()}")
    print(f"   {sensor.inspect_equipment()}")

    if vessel.status == STATUS_READY and sensor.status == STATUS_READY:
        print(f"   ✅ KIT CERTIFIED: {vessel.name} + {sensor.name} "
              f"are ready for an experiment.")
    else:
        print("   🚫 KIT REJECTED: replace the flagged item(s) before "
              "running an experiment.")
        lab.safety_log.add_entry(
            f"Kit rejected: {vessel.item_id} + {sensor.item_id}."
        )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    lab = build_default_lab()
    # STEM CONCEPT: Stoichiometric Chemical Safety & Hazard Validation —
    # every menu-2 reaction passes through Experiment.run_reaction(),
    # which validates expiry, stock, clearance, vessel, and sensor limits.
    experiment = Experiment("Acid-Base Neutralization Study")

    print(UML_CLASS_MAP)
    print("Welcome, lab manager. Type a menu number to work; 7 to exit.")

    while True:
        print(MENU)
        choice = _ask_text("Select an option (1-7): ")
        if choice == "1":
            lab.generate_inventory_report()
        elif choice == "2":
            conduct_experiment_menu(lab, experiment)
        elif choice == "3":
            lab.audit_shelf_life(30)
        elif choice == "4":
            inspect_equipment_menu(lab)
        elif choice == "5":
            add_stock_menu(lab)
        elif choice == "6":
            assemble_kit_menu(lab)
        elif choice == "7":
            print("\nPowering down the lab. Final safety log:")
            print(lab.safety_log.show())
            print("\nGoodbye — goggles off, benches wiped. 🧤")
            break
        else:
            print("❌ Invalid choice — please enter a number from 1 to 7.")


if __name__ == "__main__":
    main()
