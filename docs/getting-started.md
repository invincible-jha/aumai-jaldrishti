# Getting Started with aumai-jaldrishti

> **IMPORTANT DISCLAIMER: This tool provides estimates only. Verify with local water resource authorities and certified laboratory testing before making any water safety or infrastructure decisions.**

This guide takes you from installation to a complete panchayat water analysis in under fifteen minutes.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | Uses modern type hints |
| pip | 23+ | Or uv / poetry |
| pydantic | v2 | Installed automatically |
| click | 8+ | Installed automatically |

No database, no API keys, no internet connection required after installation.

---

## Installation

### From PyPI

```bash
pip install aumai-jaldrishti
```

### From source (development)

```bash
git clone https://github.com/aumai/aumai-jaldrishti.git
cd aumai-jaldrishti
pip install -e ".[dev]"
```

### Verify the installation

```bash
jaldrishti --version
jaldrishti --help
```

---

## Understanding the Five Analysis Areas

`aumai-jaldrishti` addresses five interconnected water resource questions. Each maps to one CLI command and one Python class:

| Question | CLI command | Core class | Standards Applied |
|---|---|---|---|
| Is the water safe to drink? | `quality` | `WaterQualityAnalyzer` | BIS 10500:2012 |
| How many households have working taps? | `fhtc` | `JJMTracker` | JJM 55 LPCD |
| Is the groundwater table sustainable? | `groundwater` | `GroundwaterMonitor` | CGWB depth categories |
| Was rainfall adequate this year? | `rainfall` | `RainfallAnalyzer` | IMD drought classification |
| Does supply meet total demand? | `budget` | `WaterBudgetPlanner` | JJM LPCD, field estimates |

The `AlertEngine` cuts across all five areas, generating alerts at four severity levels (INFO / WARNING / CRITICAL / EMERGENCY) so officials know exactly what to act on first.

---

## Step-by-Step Tutorial

This tutorial analyses a fictional village, Rajpur (panchayat ID `PAN-RAJPUR`), across all five areas.

### Step 1 — Analyse water quality

Create `rajpur_quality.json`:

```json
[
  {
    "report_id": "RPT-2025-001",
    "source_id": "BW-MAIN",
    "test_date": "2025-10-15",
    "ph": 7.1,
    "tds_ppm": 480,
    "turbidity_ntu": 1.2,
    "fluoride_ppm": 0.7,
    "arsenic_ppb": 3,
    "iron_ppm": 0.25,
    "nitrate_ppm": 28,
    "chloride_ppm": 150,
    "coliform_present": false,
    "grade": "hazardous"
  },
  {
    "report_id": "RPT-2025-002",
    "source_id": "HP-COLONY",
    "test_date": "2025-10-16",
    "ph": 8.9,
    "tds_ppm": 820,
    "turbidity_ntu": 0.5,
    "fluoride_ppm": 1.7,
    "arsenic_ppb": 0,
    "iron_ppm": 0.1,
    "nitrate_ppm": 10,
    "chloride_ppm": 200,
    "coliform_present": false,
    "grade": "hazardous"
  }
]
```

Note: the `grade` field in the JSON is overridden by the analyser's computation.

```bash
jaldrishti quality --input rajpur_quality.json
```

BW-MAIN will grade as `ACCEPTABLE` (all parameters within BIS 10500 acceptable limits). HP-COLONY will grade as `HAZARDOUS` because fluoride 1.7 ppm exceeds the permissible limit of 1.5 ppm.

**Python equivalent:**

```python
from aumai_jaldrishti import WaterQualityAnalyzer, WaterQualityReport, WaterQualityGrade

analyzer = WaterQualityAnalyzer()
report = WaterQualityReport(
    report_id="RPT-2025-002", source_id="HP-COLONY",
    test_date="2025-10-16", ph=8.9, tds_ppm=820, turbidity_ntu=0.5,
    fluoride_ppm=1.7, arsenic_ppb=0, iron_ppm=0.1, nitrate_ppm=10,
    chloride_ppm=200, coliform_present=False, grade=WaterQualityGrade.HAZARDOUS,
)
grade = analyzer.grade_report(report)              # WaterQualityGrade.HAZARDOUS
issues = analyzer.identify_contaminants(report)    # ['Fluoride: 1.7 ppm (limit 1.0)']
treatments = analyzer.recommend_treatment(report)  # ['Activated alumina or bone char defluoridation']
```

### Step 2 — Register and analyse water sources

Create `rajpur_sources.json`:

```json
[
  {
    "source_id": "BW-MAIN",
    "panchayat_id": "PAN-RAJPUR",
    "name": "Main Borewell",
    "source_type": "borewell",
    "latitude": 28.62,
    "longitude": 77.23,
    "capacity_liters_per_day": 50000,
    "current_yield_lpd": 38000,
    "depth_meters": 45,
    "is_functional": true,
    "last_tested_date": "2025-10-15"
  },
  {
    "source_id": "HP-COLONY",
    "panchayat_id": "PAN-RAJPUR",
    "name": "Colony Handpump",
    "source_type": "handpump",
    "latitude": 28.63,
    "longitude": 77.24,
    "capacity_liters_per_day": 12000,
    "current_yield_lpd": 3500,
    "depth_meters": 15,
    "is_functional": true,
    "last_tested_date": "2025-10-16"
  }
]
```

```bash
jaldrishti source --input rajpur_sources.json
```

The handpump (3500 / 12000 = 29% capacity) will be flagged as low-yield (below 40% threshold).

### Step 3 — Check JJM FHTC coverage

Create `rajpur_fhtc.json`:

```json
{
  "panchayat_id": "PAN-RAJPUR",
  "panchayat_name": "Rajpur",
  "total_households": 620,
  "fhtc_provided": 480,
  "fhtc_functional": 430,
  "target_date": "2024-03-31",
  "report_date": "2025-10-01"
}
```

```bash
jaldrishti fhtc --input rajpur_fhtc.json
```

Output: 480/620 = 77.4% coverage, 430/480 = 89.6% functional, 140 households still without tap connections.

**Python:**

```python
from aumai_jaldrishti import JJMTracker, FHTCStatus

tracker = JJMTracker()
tracker.update(FHTCStatus(
    panchayat_id="PAN-RAJPUR", panchayat_name="Rajpur",
    total_households=620, fhtc_provided=480, fhtc_functional=430,
))
status = tracker.get("PAN-RAJPUR")
print(f"Coverage: {status.coverage_pct}%")     # 77.4%
print(f"Gap: {tracker.demand_gap('PAN-RAJPUR')} households")  # 140
lpcd = tracker.lpcd_check("PAN-RAJPUR", population=2800, total_supply_lpd=141500)
print(f"LPCD: {lpcd['actual_lpcd']} (need {lpcd['required_lpcd']})")
```

### Step 4 — Monitor groundwater

Create `rajpur_groundwater.json`:

```json
[
  {"panchayat_id": "PAN-RAJPUR", "season": "pre_monsoon",  "year": 2022, "depth_meters": 11.5, "previous_year_depth": 0},
  {"panchayat_id": "PAN-RAJPUR", "season": "post_monsoon", "year": 2022, "depth_meters":  7.2, "previous_year_depth": 0},
  {"panchayat_id": "PAN-RAJPUR", "season": "pre_monsoon",  "year": 2023, "depth_meters": 13.8, "previous_year_depth": 11.5},
  {"panchayat_id": "PAN-RAJPUR", "season": "post_monsoon", "year": 2023, "depth_meters":  8.9, "previous_year_depth": 7.2},
  {"panchayat_id": "PAN-RAJPUR", "season": "pre_monsoon",  "year": 2024, "depth_meters": 16.1, "previous_year_depth": 13.8},
  {"panchayat_id": "PAN-RAJPUR", "season": "post_monsoon", "year": 2024, "depth_meters": 10.4, "previous_year_depth": 8.9}
]
```

```bash
jaldrishti groundwater --input rajpur_groundwater.json --panchayat PAN-RAJPUR
```

Pre-monsoon depths 11.5 → 13.8 → 16.1 over three consecutive years will trigger `declining_trend=True` and a WARNING alert.

### Step 5 — Analyse rainfall

Create `rajpur_rainfall.json` with monthly data for 2024. Here is the monsoon season subset (months 6–9):

```json
[
  {"panchayat_id": "PAN-RAJPUR", "month": 6, "year": 2024, "rainfall_mm":  55, "normal_mm": 110},
  {"panchayat_id": "PAN-RAJPUR", "month": 7, "year": 2024, "rainfall_mm": 120, "normal_mm": 200},
  {"panchayat_id": "PAN-RAJPUR", "month": 8, "year": 2024, "rainfall_mm":  90, "normal_mm": 180},
  {"panchayat_id": "PAN-RAJPUR", "month": 9, "year": 2024, "rainfall_mm":  40, "normal_mm": 100}
]
```

```bash
jaldrishti rainfall --input rajpur_rainfall.json --panchayat PAN-RAJPUR --year 2024
```

Monsoon total 305 mm vs normal 590 mm = -48% deviation → `moderate_drought` classification.

### Step 6 — Estimate water budget

No JSON file needed — pass parameters directly:

```bash
jaldrishti budget \
  --population 2800 \
  --livestock 350 \
  --irrigated-ha 60 \
  --supply-lpd 141500
```

Domestic demand = 154,000 LPD (2800 × 55 LPCD), agriculture ≈ 82,000 LPD, livestock = 10,500 LPD. Total demand ≈ 246,500 LPD versus 141,500 supply → deficit of ~105,000 LPD, sustainability index ≈ 57/100.

---

## Five Common Patterns

### Pattern 1 — Quality check and alert in one pass

```python
from aumai_jaldrishti import WaterQualityAnalyzer, AlertEngine
from aumai_jaldrishti import WaterQualityReport, WaterQualityGrade

analyzer = WaterQualityAnalyzer()
engine = AlertEngine()

report = WaterQualityReport(
    report_id="R001", source_id="BW-01", test_date="2025-10-01",
    ph=7.0, tds_ppm=300, turbidity_ntu=1.0,
    fluoride_ppm=2.1, arsenic_ppb=0, iron_ppm=0.2,
    nitrate_ppm=20, chloride_ppm=100,
    coliform_present=True,   # always HAZARDOUS
    grade=WaterQualityGrade.HAZARDOUS,
)
grade = analyzer.grade_report(report)
alerts = engine.check_quality(report)
for alert in alerts:
    print(f"[{alert.level.value.upper()}] {alert.message}")
# [EMERGENCY] HAZARDOUS water quality at source BW-01. Do NOT consume.
```

### Pattern 2 — Block-level FHTC coverage dashboard

```python
from aumai_jaldrishti import JJMTracker, FHTCStatus

tracker = JJMTracker()
for pid, name, total, provided, functional in [
    ("PAN-A", "Rajpur",    620, 480, 430),
    ("PAN-B", "Krishnapur", 850, 850, 790),
    ("PAN-C", "Lakshmipur", 300, 120,  90),
]:
    tracker.update(FHTCStatus(panchayat_id=pid, panchayat_name=name,
                              total_households=total,
                              fhtc_provided=provided, fhtc_functional=functional))

summary = tracker.coverage_summary()
print(f"Block average coverage: {summary['avg_coverage_pct']}%")
for s in tracker.below_target(100.0):
    print(f"  {s.panchayat_name}: {s.coverage_pct:.0f}% — {tracker.demand_gap(s.panchayat_id)} HH without tap")
```

### Pattern 3 — Groundwater decline identification

```python
from aumai_jaldrishti import GroundwaterMonitor, AlertEngine, GroundwaterLevel, SeasonType

monitor = GroundwaterMonitor()
engine = AlertEngine()

readings = [
    ("pre_monsoon", 2022, 10.0, 0.0),
    ("pre_monsoon", 2023, 12.5, 10.0),
    ("pre_monsoon", 2024, 15.1, 12.5),
]
for season_str, year, depth, prev in readings:
    monitor.add(GroundwaterLevel(
        panchayat_id="PAN-A", season=SeasonType(season_str),
        year=year, depth_meters=depth, previous_year_depth=prev,
    ))

if monitor.declining_trend("PAN-A", years=3):
    latest = monitor.latest("PAN-A")
    for alert in engine.check_groundwater(latest):
        print(f"[{alert.level.value.upper()}] {alert.message}")
print(f"Recharge potential: {monitor.recharge_potential('PAN-A')}")
```

### Pattern 4 — Water budget scenario planning

```python
from aumai_jaldrishti import WaterBudgetPlanner

planner = WaterBudgetPlanner()
budget = planner.estimate_demand(population=3000, livestock=400, irrigated_hectares=120)

for scenario_name, supply in [("Current", 100_000), ("After new borewell", 220_000)]:
    budget.total_supply_lpd = supply
    print(f"{scenario_name}: sustainability={planner.sustainability_index(budget):.0f}/100 "
          f"deficit={budget.surplus_deficit_lpd:+,.0f} LPD")
```

### Pattern 5 — Multi-year drought trend

```python
from aumai_jaldrishti import RainfallAnalyzer, RainfallRecord

analyzer = RainfallAnalyzer()

# Simulate 3 years of annual data (for demonstration)
year_data = {
    2022: (820, 950),   # (actual_mm, normal_mm)
    2023: (510, 950),
    2024: (380, 950),
}
for year, (actual, normal) in year_data.items():
    # Distribute across 12 months proportionally
    analyzer.add(RainfallRecord(
        panchayat_id="PAN-A", month=7, year=year,
        rainfall_mm=actual, normal_mm=normal,
    ))

for year in year_data:
    risk = analyzer.drought_risk("PAN-A", year)
    dev = analyzer.annual_deviation_pct("PAN-A", year)
    print(f"{year}: {risk:20s} ({dev:+.1f}%)")
```

---

## FAQ

**Q: What does "HAZARDOUS" water quality grade mean?**

The water contains at least one parameter exceeding the BIS 10500:2012 permissible limit at a level that poses an immediate health risk: coliform bacteria present; arsenic > 10 ppb; fluoride > 1.5 ppm; nitrate > 45 ppm; TDS > 2000 ppm; or pH below 5.0 or above 9.5. The water must not be consumed without treatment.

**Q: Can I trust this tool's grade without lab testing?**

No. The grade is computed from parameters you supply. Its accuracy depends entirely on your input data accuracy. This software does not replace certified laboratory testing under BIS 10500:2012 or state standards.

**Q: What is the JJM 55 LPCD standard?**

Jal Jeevan Mission mandates that every rural household receive a Functional Household Tap Connection supplying at least 55 litres per capita per day of safe water. This covers drinking, cooking, and basic hygiene. The WHO minimum for basic access is 20 LPCD.

**Q: Why does `WaterBudget.total_supply_lpd` default to 0?**

`WaterBudgetPlanner.estimate_demand()` computes demand only. Set `budget.total_supply_lpd` to your measured supply before calling `sustainability_index()` or reading `surplus_deficit_lpd`.

**Q: Why does `monsoon_performance` use months 6–9?**

These are India's southwest monsoon months for most of the country. `RainfallAnalyzer.monsoon_performance()` sums `rainfall_mm` and `normal_mm` for months 6–9 only. Monsoon performance is the dominant driver of groundwater recharge and kharif crop irrigation.

**Q: How is `declining_trend` calculated?**

It filters for `SeasonType.PRE_MONSOON` records only (the worst-case annual depth) and checks whether `depth_meters` increased in every consecutive year over the last `years` records. This requires at least 2 matching records.

**Q: What does `recharge_potential` mean?**

It compares pre-monsoon depth (deepest point of the year) to post-monsoon depth (shallowest, after monsoon recharge) for the same year: `recovery = pre_depth - post_depth`. Recovery > 5m = `"high"`, 2–5m = `"moderate"`, 0–2m = `"low"`, ≤0 = `"negligible"`.

**Q: The `quality` command shows "safe" but the water is visibly discoloured.**

The grader only evaluates the parameters in `WaterQualityReport`. If `turbidity_ntu` was not filled or was set to 0, turbidity will not trigger a contamination flag. Always populate all measured parameters. Visible discolouration may indicate parameters not yet in the model (colour, odour, temperature) — consult a certified laboratory.

---

## Next Steps

- [API Reference](api-reference.md) — complete signatures for every public class and method
- [examples/quickstart.py](../examples/quickstart.py) — runnable demo
- [CONTRIBUTING.md](../CONTRIBUTING.md) — how to add water parameters or standards
