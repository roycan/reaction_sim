# 🧪 Digital Science Lab — Inventory & Reaction Simulator

An interactive terminal "Science Lab" exemplar project for **Grade 9 CS
students** learning Object-Oriented Programming. It models lab equipment,
chemical shelf-life tracking, and experiment safety rules — with zero
external dependencies (pure standard-library Python).

**Requirement:** Python 3.9+ · **No pip installs needed**

---

## 🚀 Quick Start

```bash
cd reaction_sim
python main.py
```

Try this first-run tour:

1. **Menu 1** — view the inventory (note: the Hydrogen Peroxide is already
   ⚠ EXPIRED by design, so every feature has something to show).
2. **Menu 2** — run `HCL-001` + `NAOH-001` (50 ml each) in the Beaker with
   the Temperature Sensor → a safe neutralization (~95 °C).
3. **Menu 2 again** — repeat with **125 ml each** → heat spikes to ~200 °C,
   which **exceeds the sensor's 120 °C limit** → the reaction aborts and
   nothing is consumed.
4. **Menu 3** — shelf-life audit advances the lab clock 30 days and flags
   the expired peroxide for hazardous-waste disposal.
5. **Menu 4** — one polymorphic loop inspects all equipment: glassware
   reports cracks, sensors report calibration.
6. **Menu 6** — assemble an experiment kit: pick a vessel + sensor and the
   app certifies the pair via each object's own `inspect_equipment()`
   implementation. Choose the cracked flask or the uncalibrated pH sensor
   to see a rejection.

**Teacher tip:** to demonstrate abstract-class enforcement live, run
`python3 -c "from equipment import Equipment; Equipment('X-000', 'Mystery')"`
in a terminal — Python raises `TypeError` on the spot.

---

## 📁 Project Structure & OOP Concept Map

| File | Primary Concepts | What to Notice |
|------|------------------|----------------|
| [`chemical.py`](chemical.py) | **Encapsulation** | `days_stored` is owned by the bottle; `use_quantity()` guarantees volume never drops below 0 |
| [`equipment.py`](equipment.py) | **ABCs, Inheritance, Polymorphism** | `@abstractmethod inspect_equipment()`; two `super().__init__()` patterns (forwarded name vs. derived name) |
| [`inventory.py`](inventory.py) | **Aggregation vs. Composition** | Chemicals/equipment are stored **by reference** (◇ aggregation); the `SafetyLog` is **created and owned** inside `LabInventory.__init__` (◆ composition) |
| [`experiment.py`](experiment.py) | **Dependency Injection, Exception Inheritance, Data-driven Design** | `run_reaction()` receives its objects as parameters; `SafetyViolationError` extends `Exception`; `REACTION_RULES` is a dict keyed by `frozenset` |
| [`main.py`](main.py) | **Integration** | ASCII UML diagram up top; validated input loops; kit assembly certified by the abstract contract |

Design decisions and the full reaction-rule matrix are pinned in
[`plans/reaction_sim_plan.md`](plans/reaction_sim_plan.md).

---

## 🗺️ Suggested Lesson Sequence

Each file only uses concepts introduced *before* it:

1. **`chemical.py`** — classes, `__init__`, attributes, methods that guard state (encapsulation), returning `bool` for success/failure.
2. **`equipment.py`** — inheritance, `super()`, abstract base classes, why Python *forces* subclasses to implement `inspect_equipment()`.
3. **`inventory.py`** — collections of objects; the crucial difference between *aggregating* references and *composing* owned parts.
4. **`experiment.py`** — dependency injection ("borrow, don't build"), custom exceptions, replacing `if/elif` chains with a lookup table.
5. **`main.py`** — wiring it together, input validation, polymorphism in one loop, and kit certification driven by the abstract contract.

---

## 🛡️ Safety Model (STEM Concepts)

- **Shelf life:** each bottle tracks its own age; expired stock is
  quarantined for disposal and can never enter a reaction.
- **Hazard clearance:** any **Oxidizer** demands `Advanced` clearance.
- **Forbidden combinations:** `Oxidizer + Acid` is always rejected.
- **Heat model:** `final_temp = 25 °C + heat_per_ml × total_ml` — doubling
  the dose can push a "safe" reaction past the sensor limit (dose control!).
- **Abort semantics:** every rejection raises `SafetyViolationError`; a
  blocked reaction consumes **zero** stock.

---

## 🎯 Ideas for Your Own Project (Extension Menu)

Pick one or more to make this codebase *yours*:

- **New equipment subclass** — `BunsenBurner` or `HotPlate` with its own
  `inspect_equipment()`; the inventory loop should pick it up automatically.
- **New reaction rules** — add entries to `REACTION_RULES` (one dict entry,
  no new `if/elif`).
- **`@property` validation** — make `Chemical.volume_ml` reject negative
  assignments at the attribute level.
- **Persistence** — save/load the inventory to JSON with `json.dump`.
- **Testing** — turn the smoke checks into real `pytest` tests.
- **Better CLI** — color output with ANSI codes, or a `curses` interface.

### Rubric hooks

| Skill | Evidence in this project |
|-------|--------------------------|
| Encapsulation | `use_quantity()` guards (`chemical.py`) |
| Inheritance & ABCs | `Equipment`/`Glassware`/`Sensor` (`equipment.py`) |
| Composition vs. aggregation | `SafetyLog` vs. chemical dict (`inventory.py`) |
| Dependency injection | `run_reaction()` parameters (`experiment.py`) |
| Polymorphism | one inspect loop over mixed subclasses (`main.py`) |
| Exception design | `SafetyViolationError` hierarchy (`experiment.py`) |
