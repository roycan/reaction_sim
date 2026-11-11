"""
experiment.py — Reaction Rules & Safety Checks (Dependency)
===========================================================

Models a scientist running a reaction by PASSING IN the objects the
reaction needs (two chemicals, a vessel, a sensor). The Experiment class
owns NONE of them — it only borrows them for the duration of one method
call.

OOP CONCEPTS DEMONSTRATED
-------------------------
* Dependency Injection   — run_reaction() RECEIVES a Chemical, Glassware,
                           and Sensor. The Experiment never constructs
                           them itself; it works with whatever the caller
                           provides (dashed ..> USES-A arrows in the UML).
* Data-driven design     — REACTION_RULES is a plain dict; adding a new
                           rule is ONE new dict entry, not another
                           if/elif branch.
* Exception inheritance  — SafetyViolationError extends Exception, so a
                           caller can catch EVERY safety abort with a
                           single `except` clause.

STEM CONCEPT: Stoichiometric Chemical Safety & Hazard Validation
----------------------------------------------------------------
* Real labs forbid certain combinations outright (oxidizer + acid).
* Heat scales with VOLUME — doubling the dose can push an otherwise
  "safe" reaction past what the sensor and vessel can handle.
"""

from chemical import Chemical
from equipment import Glassware, Sensor, STATUS_READY

AMBIENT_TEMP_C = 25.0

# ---------------------------------------------------------------------------
# STEM CONCEPT: hazard validation table.
# The keys are frozensets, so {"Acid", "Base"} and {"Base", "Acid"} are the
# SAME key — reaction rules must not depend on argument order.
# heat_per_ml == 0.0  → nothing happens, nothing is dispensed.
# ---------------------------------------------------------------------------
REACTION_RULES = {
    frozenset({"Acid", "Base"}): {
        "name": "Neutralization",
        "heat_per_ml": 0.7,
        "note": "salt and water form; the mixture heats up noticeably",
    },
    frozenset({"Acid", "Acid"}): {
        "name": "No Reaction",
        "heat_per_ml": 0.0,
        "note": "same-class mixing: nothing happens, volumes preserved",
    },
    frozenset({"Base", "Base"}): {
        "name": "No Reaction",
        "heat_per_ml": 0.0,
        "note": "same-class mixing: nothing happens, volumes preserved",
    },
    frozenset({"Oxidizer", "Acid"}): {
        "name": "FORBIDDEN",
        "heat_per_ml": None,
        "note": "violent oxidation risk — banned by lab safety policy",
    },
    frozenset({"Oxidizer", "Base"}): {
        "name": "Vigorous Exothermic",
        "heat_per_ml": 0.5,
        "note": "strong heat release — monitor the sensor closely",
    },
    frozenset({"Oxidizer", "Oxidizer"}): {
        "name": "Unstable Mixture",
        "heat_per_ml": 0.6,
        "note": "unstable combination — only small doses permitted",
    },
    frozenset({"Inert", "Acid"}): {
        "name": "Dilution",
        "heat_per_ml": 0.0,
        "note": "no measurable reaction, volumes preserved",
    },
    frozenset({"Inert", "Base"}): {
        "name": "Dilution",
        "heat_per_ml": 0.0,
        "note": "no measurable reaction, volumes preserved",
    },
    frozenset({"Inert", "Oxidizer"}): {
        "name": "Dilution",
        "heat_per_ml": 0.0,
        "note": "no measurable reaction, volumes preserved",
    },
    frozenset({"Inert", "Inert"}): {
        "name": "No Reaction",
        "heat_per_ml": 0.0,
        "note": "nothing happens, volumes preserved",
    },
}


class SafetyViolationError(Exception):
    """
    Raised when a reaction would break a lab safety rule.

    OOP CONCEPT: this class INHERITS from Exception. Creating a custom
    exception type lets callers catch ALL safety aborts with one line:
    `except SafetyViolationError as err:` — while still being a normal
    Python exception underneath.
    """


class Experiment:
    """One planned reaction with a hazard-clearance requirement."""

    def __init__(self, title: str, required_hazard_clearance: str = "Basic") -> None:
        self.title = title
        self.required_hazard_clearance = required_hazard_clearance
        self.is_completed = False

    # ------------------------------------------------------------------
    # OOP CONCEPT: Dependency Injection (Experiment USES-A Chemical &
    # Equipment — they are PARAMETERS here, not attributes built inside).
    # The caller decides which real objects to lend to this method.
    # ------------------------------------------------------------------
    def run_reaction(
        self,
        chem1: Chemical,
        chem2: Chemical,
        vessel: Glassware,
        temp_sensor: Sensor,
        dose_ml: float = 25.0,
    ) -> str:
        """
        Attempt the reaction under full safety supervision.

        Pipeline — ANY failure raises SafetyViolationError and NOTHING is
        dispensed (a failed run consumes no stock):
            0. reject expired reagents
            1. confirm both bottles hold enough stock
            2. check hazard clearance (oxidizers need 'Advanced')
            3. vessel must be intact and large enough
            4. sensor must be calibrated
            5. look up the reaction rule
            6. simulate heat; trip-wire the sensor limit
            7. dispense both doses and mark the experiment complete
        """
        self._check_expiry(chem1, chem2)           # Step 0
        self._check_stock(chem1, chem2, dose_ml)   # Step 1
        self._check_clearance(chem1, chem2)        # Step 2
        self._check_vessel(vessel, dose_ml)        # Step 3
        self._check_sensor(temp_sensor)            # Step 4
        rule = self._lookup_rule(chem1, chem2)     # Step 5

        if rule["heat_per_ml"] == 0.0:
            # Nothing happens — keep every drop in the bottles.
            return (f"🧪 {chem1.name} + {chem2.name}: {rule['name']} — "
                    f"{rule['note']}. No volumes were consumed.")

        final_temp, reading = self._simulate_heat(          # Step 6
            rule, dose_ml, temp_sensor
        )
        chem1.use_quantity(dose_ml)                          # Step 7
        chem2.use_quantity(dose_ml)
        self.is_completed = True

        return (
            f"✅ REACTION COMPLETE — {rule['name']}\n"
            f"   {chem1.name} + {chem2.name}: {rule['note']}.\n"
            f"   Dispensed {dose_ml:.1f} ml from each bottle into {vessel.name}.\n"
            f"   Predicted temp: {final_temp:.1f} °C | "
            f"{temp_sensor.name} reading: {reading} °C\n"
            f"   Remaining stock: {chem1.volume_ml:.1f} ml / "
            f"{chem2.volume_ml:.1f} ml"
        )

    # ==================================================================
    # Private validation helpers (single responsibility each).
    # Every abort raises SafetyViolationError — printing happens in main.
    # ==================================================================

    def _check_expiry(self, chem1: Chemical, chem2: Chemical) -> None:
        """Step 0 — expired reagents are never allowed near a reaction."""
        for chem in (chem1, chem2):
            if chem.is_expired():
                raise SafetyViolationError(
                    f"{chem.name} [{chem.chemical_id}] is EXPIRED "
                    f"({chem.days_stored} days stored > {chem.shelf_life_days} "
                    f"day shelf life). Quarantine it for hazardous-waste disposal."
                )

    def _check_stock(self, chem1: Chemical, chem2: Chemical, dose_ml: float) -> None:
        """Step 1 — both bottles must hold the full dose."""
        for chem in (chem1, chem2):
            if chem.volume_ml < dose_ml:
                raise SafetyViolationError(
                    f"Insufficient stock: {chem.name} has only "
                    f"{chem.volume_ml:.1f} ml but the reaction needs "
                    f"{dose_ml:.1f} ml."
                )

    def _check_clearance(self, chem1: Chemical, chem2: Chemical) -> None:
        """Step 2 — oxidizers demand 'Advanced' hazard clearance."""
        grades = {chem1.hazard_grade, chem2.hazard_grade}
        if "Oxidizer" in grades and self.required_hazard_clearance != "Advanced":
            raise SafetyViolationError(
                f"Oxidizers require 'Advanced' clearance, but '{self.title}' "
                f"only holds '{self.required_hazard_clearance}' clearance."
            )

    def _check_vessel(self, vessel: Glassware, dose_ml: float) -> None:
        """Step 3 — intact glass, and big enough for the combined dose."""
        if vessel.status != STATUS_READY:
            raise SafetyViolationError(
                f"{vessel.name} [{vessel.item_id}] is not usable — "
                f"status: {vessel.status}."
            )
        total_ml = 2 * dose_ml
        if total_ml > vessel.capacity_ml:
            raise SafetyViolationError(
                f"{total_ml:.1f} ml of reactants exceeds {vessel.name} "
                f"capacity ({vessel.capacity_ml} ml)."
            )

    def _check_sensor(self, temp_sensor: Sensor) -> None:
        """Step 4 — never trust an uncalibrated sensor for safety limits."""
        if temp_sensor.status != STATUS_READY:
            raise SafetyViolationError(
                f"{temp_sensor.name} is '{temp_sensor.status}' — "
                f"recalibrate before running safety-critical reactions."
            )

    def _lookup_rule(self, chem1: Chemical, chem2: Chemical) -> dict:
        """Step 5 — find the rule for this hazard pair (order-independent)."""
        key = frozenset({chem1.hazard_grade, chem2.hazard_grade})
        rule = REACTION_RULES.get(key)
        if rule is None:
            return {
                "name": "No Reaction",
                "heat_per_ml": 0.0,
                "note": "these hazard classes are not known to react",
            }
        if rule["name"] == "FORBIDDEN":
            raise SafetyViolationError(
                f"FORBIDDEN COMBINATION ({chem1.hazard_grade} + "
                f"{chem2.hazard_grade}): {rule['note']}."
            )
        return rule

    def _simulate_heat(
        self, rule: dict, dose_ml: float, temp_sensor: Sensor
    ) -> tuple:
        """
        Step 6 — deterministic heat model + sensor trip-wire.

        STEM CONCEPT: heat scales with VOLUME (dose control matters).
            heat_c     = heat_per_ml × total volume
            final_temp = room temperature + heat_c
        """
        total_ml = 2 * dose_ml
        heat_c = rule["heat_per_ml"] * total_ml
        final_temp = AMBIENT_TEMP_C + heat_c

        if final_temp > temp_sensor.max_temp_c:
            raise SafetyViolationError(
                f"HEAT SPIKE: predicted {final_temp:.1f} °C exceeds "
                f"{temp_sensor.name} limit "
                f"({temp_sensor.max_temp_c:.0f} °C)."
            )

        reading = temp_sensor.take_reading(final_temp)
        return final_temp, reading
