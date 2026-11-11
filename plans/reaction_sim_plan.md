# Implementation Plan — Digital Science Lab Inventory & Reaction Simulator

Pinned design decisions from the approved spec review. Every number and rule
below is FINAL — implementation files must match this document exactly.

## Pinned design decisions

| #  | Decision |
|----|----------|
| D1 | Composition honesty: `LabInventory` creates and OWNS a `SafetyLog` internally (composition `*--`). Chemicals/equipment are stored by reference only (aggregation `o--`). |
| D2 | `run_reaction()` Step 0 checks `chem.is_expired()` — expired stock is rejected BEFORE anything else happens. |
| D3 | `Chemical.days_stored` is an ATTRIBUTE; `is_expired()` takes no arguments; only `audit_shelf_life(days_elapsed)` advances the lab clock (`days_stored += days_elapsed`). |
| D4 | (REVISED) Menu 6 = Assemble an Experiment Kit: vessel + sensor certified via inspect_equipment(). The ABC-instantiation demo was removed from the CLI (broke the lab narrative); teachers demo the TypeError live in a REPL instead. |
| D5 | `required_hazard_clearance` is enforced: any Oxidizer in a reaction requires clearance `"Advanced"`. |
| D6 | ALL aborts (expired, low stock, wrong clearance, cracked vessel, over-capacity, uncalibrated sensor, forbidden pair, sensor heat trip) raise `SafetyViolationError`. Aborts dispense NOTHING and never set `is_completed`. |
| D7 | No-reaction combos (`heat_per_ml == 0.0`) consume nothing — volumes preserved. |
| D8 | `run_reaction(..., dose_ml: float = 25.0)` — optional extra parameter (spec signature preserved); makes vessel capacity + sensor limits demonstrable. |
| D9 | Heat model: `heat_c = heat_per_ml × (2 × dose_ml)`; `final_temp = 25.0 + heat_c`; trip-wire if `final_temp > temp_sensor.max_temp_c`. |
| D10 | Seed data exercises every feature: expired peroxide (400/180 days), cracked flask, uncalibrated pH sensor. |

## Reaction rule matrix (dict keyed by frozenset)

| Hazard pair         | Rule name           | heat_per_ml | Behaviour                          |
|---------------------|---------------------|-------------|------------------------------------|
| Acid + Base         | Neutralization      | 0.7         | heat spike; volumes dispensed      |
| Acid + Acid         | No Reaction         | 0.0         | nothing happens, nothing dispensed |
| Base + Base         | No Reaction         | 0.0         | nothing happens, nothing dispensed |
| Oxidizer + Acid     | FORBIDDEN           | —           | `SafetyViolationError`, always     |
| Oxidizer + Base     | Vigorous Exothermic | 0.5         | heat; volumes dispensed            |
| Oxidizer + Oxidizer | Unstable Mixture    | 0.6         | heat; volumes dispensed            |
| Inert + anything    | Dilution            | 0.0         | nothing happens, nothing dispensed |

Demo math: 50 ml + 50 ml acid+base → heat 70 → 95 °C ≤ 120 °C sensor limit → success.
Scaled up: 125 ml + 125 ml → heat 175 → 200 °C > 120 °C → sensor-trip abort.
Unknown pair (missing dict key) → treated as "No Reaction", nothing dispensed.

## Class contracts (quick reference)

- **chemical.py** — `HAZARD_GRADES`, `Chemical` (`is_expired()`, `use_quantity() -> bool`, `get_safety_label() -> str`, `__str__`)
- **equipment.py** — `STATUS_READY/_CRACKED/_UNCALIBRATED`, `Equipment(ABC)` + `@abstractmethod inspect_equipment() -> str`, `Glassware(capacity_ml)`, `Sensor(sensor_type, max_temp_c)` + `take_reading(base_temp_c) -> float`
- **inventory.py** — `SafetyLog` (composition-owned), `LabInventory` (`add_chemical`, `add_equipment` with duplicate-ID rejection, `find_chemical`, `find_equipment`, `glassware_items`, `sensors`, `audit_shelf_life(days_elapsed) -> list[Chemical]`, `generate_inventory_report()`)
- **experiment.py** — `REACTION_RULES`, `AMBIENT_TEMP_C = 25.0`, `SafetyViolationError(Exception)`, `Experiment.run_reaction()` pipeline: expiry → stock → clearance → vessel → sensor → rule lookup → heat/sensor-limit → dispense; decomposed into private `_check_*` / `_lookup_rule` / `_simulate_heat` helpers
- **main.py** — ASCII UML header, seed inventory (below), 7-item menu, `_ask_float` / `_ask_int` validators, polymorphic inspect loop (`for item in equipment_list: item.inspect_equipment()`), ABC-crash demo in `try/except TypeError`

## Seed data

| ID       | Item                     | Key values                        | Demonstrates            |
|----------|--------------------------|-----------------------------------|-------------------------|
| HCL-001  | Hydrochloric Acid (HCl)  | 500 ml, Acid, 900 d shelf, 120 d  | baseline stock          |
| NAOH-001 | Sodium Hydroxide (NaOH)  | 500 ml, Base, 730 d, 80 d         | acid+base demo          |
| H2O-001  | Distilled Water (H2O)    | 1000 ml, Inert, 9999 d, 10 d      | dilution / no-op rules  |
| H2O2-001 | Hydrogen Peroxide (H2O2) | 300 ml, Oxidizer, 180 d, 400 d    | EXPIRED flag            |
| GLS-001  | Beaker, 250 ml           | Ready                             | normal vessel           |
| GLS-002  | Erlenmeyer Flask, 100 ml | Cracked                           | vessel rejection        |
| SEN-001  | Temperature Sensor       | max 120 °C, Ready                 | reaction sensor         |
| SEN-002  | pH Sensor                | max 60 °C, Needs Calibration      | calibration rejection   |

## Smoke-test checklist (task 7)

1. Menu 6 → kit assembly certifies GLS-001 + SEN-001; rejects GLS-002 (cracked) and SEN-002 (uncalibrated)
2. Reaction with H2O2-001 → expired rejection (Step 0)
3. Fresh Oxidizer + Base with "Basic" clearance → clearance rejection
4. Oxidizer + Acid under "Advanced" clearance → FORBIDDEN rule rejection
5. HCl + NaOH, 50 ml each, SEN-001, GLS-001 → success; volumes 450/450
6. HCl + NaOH, 125 ml each → heat 175 → 200 °C > 120 °C → sensor abort; volumes unchanged
7. Cracked flask (GLS-002) rejected as vessel; uncalibrated SEN-002 rejected as sensor
8. Acid + Acid → "No Reaction", volumes unchanged
9. Audit (+30 days) → H2O2-001 flagged for hazardous-waste disposal; report renders aligned tables
