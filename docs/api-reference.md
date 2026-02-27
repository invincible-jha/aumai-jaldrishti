# API Reference — aumai-jaldrishti

> **Water Disclaimer:** This tool provides estimates only. Always verify with local water
> resource authorities and certified laboratory testing before making decisions.

Package: `aumai_jaldrishti` | Version: 0.1.0 | Python: 3.11+

---

## Module: `aumai_jaldrishti.models`

All models use Pydantic v2. Validation is enforced at construction time.

---

### `WaterSourceType`

Enum of water source types.

```python
class WaterSourceType(str, Enum):
    BOREWELL = "borewell"
    HANDPUMP = "handpump"
    OPEN_WELL = "open_well"
    RIVER = "river"
    POND = "pond"
    SPRING = "spring"
    RESERVOIR = "reservoir"
    RAINWATER = "rainwater"
    PIPELINE = "pipeline"
```

---

### `WaterQualityGrade`

Enum of water quality grades.

```python
class WaterQualityGrade(str, Enum):
    SAFE = "safe"
    ACCEPTABLE = "acceptable"
    CONTAMINATED = "contaminated"
    HAZARDOUS = "hazardous"
```

Ordered by severity: `SAFE < ACCEPTABLE < CONTAMINATED < HAZARDOUS`.

---

### `SeasonType`

Enum of hydrological seasons.

```python
class SeasonType(str, Enum):
    PRE_MONSOON = "pre_monsoon"
    MONSOON = "monsoon"
    POST_MONSOON = "post_monsoon"
    WINTER = "winter"
```

---

### `AlertLevel`

Enum of alert severity levels.

```python
class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"
```

---

### `WaterSource`

A physical water source at a panchayat.

```python
class WaterSource(BaseModel):
    source_id: str
    panchayat_id: str
    name: str
    source_type: WaterSourceType
    latitude: float
    longitude: float
    capacity_liters_per_day: float
    current_yield_lpd: float
    depth_meters: float = 0
    is_functional: bool = True
    last_tested_date: str = ""

    @property
    def yield_pct(self) -> float: ...
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `source_id` | `str` | required | Unique identifier |
| `panchayat_id` | `str` | required | Panchayat this source belongs to |
| `name` | `str` | required | Human-readable name |
| `source_type` | `WaterSourceType` | required | Type enum value |
| `latitude` | `float` | -90 to 90 | GPS latitude |
| `longitude` | `float` | -180 to 180 | GPS longitude |
| `capacity_liters_per_day` | `float` | >= 0 | Design capacity in LPD |
| `current_yield_lpd` | `float` | >= 0 | Current measured yield in LPD |
| `depth_meters` | `float` | >= 0, default `0` | Depth (for borewells/wells) |
| `is_functional` | `bool` | default `True` | Whether source is currently operational |
| `last_tested_date` | `str` | default `""` | ISO date string of last water test |

**Properties:**

#### `yield_pct`

```python
@property
def yield_pct(self) -> float
```

Current yield as a percentage of capacity. Returns `0.0` if `capacity_liters_per_day == 0`.

Formula: `round((current_yield_lpd / capacity_liters_per_day) * 100, 1)`

---

### `WaterQualityReport`

Laboratory test results for a water source.

```python
class WaterQualityReport(BaseModel):
    report_id: str
    source_id: str
    test_date: str
    ph: float
    tds_ppm: float
    turbidity_ntu: float
    chloride_ppm: float = 0
    fluoride_ppm: float = 0
    arsenic_ppb: float = 0
    iron_ppm: float = 0
    nitrate_ppm: float = 0
    coliform_present: bool = False
    grade: WaterQualityGrade = WaterQualityGrade.HAZARDOUS
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `report_id` | `str` | required | Unique report identifier |
| `source_id` | `str` | required | Source this report belongs to |
| `test_date` | `str` | required | ISO date string |
| `ph` | `float` | 0 to 14 | pH measurement |
| `tds_ppm` | `float` | >= 0 | Total dissolved solids in ppm |
| `turbidity_ntu` | `float` | >= 0 | Turbidity in NTU |
| `chloride_ppm` | `float` | >= 0, default `0` | Chloride in ppm |
| `fluoride_ppm` | `float` | >= 0, default `0` | Fluoride in ppm |
| `arsenic_ppb` | `float` | >= 0, default `0` | Arsenic in ppb |
| `iron_ppm` | `float` | >= 0, default `0` | Iron in ppm |
| `nitrate_ppm` | `float` | >= 0, default `0` | Nitrate in ppm |
| `coliform_present` | `bool` | default `False` | Whether coliform bacteria detected |
| `grade` | `WaterQualityGrade` | default `HAZARDOUS` | Grade (overridden by `WaterQualityAnalyzer.grade_report`) |

Note: the `grade` field stored in the model is informational only. Always call
`WaterQualityAnalyzer.grade_report(report)` to compute the authoritative grade.

---

### `FHTCStatus`

Functional Household Tap Connection status per Jal Jeevan Mission.

```python
class FHTCStatus(BaseModel):
    panchayat_id: str
    panchayat_name: str
    total_households: int
    fhtc_provided: int
    fhtc_functional: int
    target_date: str = ""
    report_date: str = ""

    @property
    def coverage_pct(self) -> float: ...

    @property
    def functional_pct(self) -> float: ...
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `panchayat_id` | `str` | required | Panchayat identifier |
| `panchayat_name` | `str` | required | Human-readable name |
| `total_households` | `int` | >= 0 | Total households in panchayat |
| `fhtc_provided` | `int` | >= 0 | Tap connections installed |
| `fhtc_functional` | `int` | >= 0 | Tap connections currently functional |
| `target_date` | `str` | default `""` | JJM target completion date |
| `report_date` | `str` | default `""` | Date of this status report |

**Properties:**

#### `coverage_pct`

```python
@property
def coverage_pct(self) -> float
```

FHTC coverage as percentage of total households.
Formula: `round((fhtc_provided / total_households) * 100, 1)`.
Returns `0.0` if `total_households == 0`.

#### `functional_pct`

```python
@property
def functional_pct(self) -> float
```

Functional connections as percentage of provided connections.
Formula: `round((fhtc_functional / fhtc_provided) * 100, 1)`.
Returns `0.0` if `fhtc_provided == 0`.

---

### `GroundwaterLevel`

Seasonal groundwater depth measurement.

```python
class GroundwaterLevel(BaseModel):
    panchayat_id: str
    season: SeasonType
    year: int
    depth_meters: float
    previous_year_depth: float = 0

    @property
    def change_meters(self) -> float: ...

    @property
    def is_declining(self) -> bool: ...
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `panchayat_id` | `str` | required | Panchayat identifier |
| `season` | `SeasonType` | required | Season of measurement |
| `year` | `int` | required | Year of measurement |
| `depth_meters` | `float` | >= 0 | Current depth to groundwater table in metres |
| `previous_year_depth` | `float` | >= 0, default `0` | Same season depth the previous year |

**Properties:**

#### `change_meters`

Year-over-year change: `round(depth_meters - previous_year_depth, 2)`.
Positive means the table is deeper (declining); negative means shallower (rising).

#### `is_declining`

`True` if `depth_meters > previous_year_depth` (table is deeper than last year).

---

### `WaterAlert`

A generated water-related alert.

```python
class WaterAlert(BaseModel):
    alert_id: str
    panchayat_id: str
    level: AlertLevel
    category: str
    message: str
    source_id: str = ""
    date: str = ""
    is_active: bool = True
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `alert_id` | `str` | Sequential ID, e.g. `"ALERT-0001"` |
| `panchayat_id` | `str` | Panchayat the alert applies to |
| `level` | `AlertLevel` | Severity level |
| `category` | `str` | Alert category: `"water_quality"`, `"groundwater"`, `"groundwater_trend"`, `"supply"`, `"drought"`, `"flood"` |
| `message` | `str` | Human-readable alert message |
| `source_id` | `str` | Source ID if alert is source-specific |
| `date` | `str` | Alert date |
| `is_active` | `bool` | Whether alert is still active |

---

### `WaterBudget`

Water demand and supply budget for a panchayat.

```python
class WaterBudget(BaseModel):
    panchayat_id: str
    year: int
    total_demand_lpd: float
    total_supply_lpd: float
    domestic_demand_lpd: float
    agriculture_demand_lpd: float
    industrial_demand_lpd: float

    @property
    def surplus_deficit_lpd(self) -> float: ...

    @property
    def is_deficit(self) -> bool: ...
```

**Properties:**

#### `surplus_deficit_lpd`

`round(total_supply_lpd - total_demand_lpd, 0)`. Positive = surplus; negative = deficit.

#### `is_deficit`

`True` if `total_supply_lpd < total_demand_lpd`.

---

### `RainfallRecord`

Monthly rainfall measurement.

```python
class RainfallRecord(BaseModel):
    panchayat_id: str
    month: int
    year: int
    rainfall_mm: float
    normal_mm: float

    @property
    def deviation_pct(self) -> float: ...
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `panchayat_id` | `str` | required | Panchayat identifier |
| `month` | `int` | 1 to 12 | Month (1=January, 12=December) |
| `year` | `int` | required | Year |
| `rainfall_mm` | `float` | >= 0 | Actual rainfall in mm |
| `normal_mm` | `float` | >= 0 | Climatological normal for this month in mm |

**Properties:**

#### `deviation_pct`

`round(((rainfall_mm - normal_mm) / normal_mm) * 100, 1)`. Returns `0.0` if `normal_mm == 0`.

---

## Module: `aumai_jaldrishti.core`

---

### `JJM_LPCD_STANDARD`

```python
JJM_LPCD_STANDARD: int = 55
```

Jal Jeevan Mission per-capita daily supply target in litres.

---

### `_BIS_LIMITS`

```python
_BIS_LIMITS: dict[str, float]
```

BIS 10500:2012 drinking water standards used by `WaterQualityAnalyzer`.

| Key | Value | Unit |
|-----|-------|------|
| `ph_min` | 6.5 | — |
| `ph_max` | 8.5 | — |
| `tds_acceptable` | 500 | ppm |
| `tds_permissible` | 2000 | ppm |
| `turbidity_acceptable` | 1 | NTU |
| `turbidity_permissible` | 5 | NTU |
| `chloride_acceptable` | 250 | ppm |
| `chloride_permissible` | 1000 | ppm |
| `fluoride_acceptable` | 1.0 | ppm |
| `fluoride_permissible` | 1.5 | ppm |
| `arsenic_max_ppb` | 10 | ppb |
| `iron_acceptable` | 0.3 | ppm |
| `iron_permissible` | 1.0 | ppm |
| `nitrate_max` | 45 | ppm |

---

### `WaterQualityAnalyzer`

Analyse water quality against BIS 10500:2012 standards.

```python
class WaterQualityAnalyzer:
```

No constructor parameters.

**Methods:**

#### `grade_report`

```python
def grade_report(self, report: WaterQualityReport) -> WaterQualityGrade
```

Assign quality grade based on BIS limits.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report` | `WaterQualityReport` | Quality report to grade |

Returns: `WaterQualityGrade`

**Grading logic:**

Sets internal `hazardous` and `contaminated` flags then returns:

- `HAZARDOUS` if `hazardous` is True
- `CONTAMINATED` if `contaminated` is True (and not hazardous)
- `SAFE` if all parameters are within acceptable limits
- `ACCEPTABLE` if all parameters are within permissible but not all within acceptable limits

Parameters that set `hazardous=True`: pH < 5.0 or > 9.5; TDS > 2000 ppm; fluoride > 1.5 ppm;
arsenic > 10 ppb; nitrate > 45 ppm; coliform present.

Parameters that set `contaminated=True`: pH outside 6.5–8.5; TDS 500–2000 ppm; turbidity > 5 NTU;
fluoride 1.0–1.5 ppm; iron > 1.0 ppm.

---

#### `identify_contaminants`

```python
def identify_contaminants(self, report: WaterQualityReport) -> list[str]
```

List parameters exceeding BIS acceptable limits with measured vs limit values.

Returns: `list[str]`, empty if all within acceptable limits.

---

#### `recommend_treatment`

```python
def recommend_treatment(self, report: WaterQualityReport) -> list[str]
```

Suggest treatment technologies based on detected contaminants.

Returns: `list[str]` of treatment recommendations.

| Contaminant | Treatment |
|-------------|-----------|
| Coliform | Chlorination or UV disinfection |
| High TDS | Reverse osmosis (RO) |
| High fluoride | Activated alumina or bone char defluoridation |
| High arsenic | Arsenic removal plant (oxidation + adsorption) |
| High iron | Aeration and filtration |
| High turbidity | Slow sand filtration or coagulation-flocculation |
| High nitrate | Ion exchange or biological denitrification |
| Low pH | Lime dosing |
| High pH | Acid dosing or CO2 injection |

---

### `SourceManager`

Manage and monitor water sources for a panchayat.

```python
class SourceManager:
    def __init__(self) -> None: ...
```

**Methods:**

#### `register`

```python
def register(self, source: WaterSource) -> None
```

Register a water source. Overwrites if `source_id` already exists.

#### `get`

```python
def get(self, source_id: str) -> WaterSource | None
```

Get a source by ID. Returns `None` if not found.

#### `by_panchayat`

```python
def by_panchayat(self, panchayat_id: str) -> list[WaterSource]
```

All sources (functional and non-functional) for a panchayat.

#### `by_type`

```python
def by_type(self, source_type: WaterSourceType) -> list[WaterSource]
```

All sources of a given type across all panchayats.

#### `functional_sources`

```python
def functional_sources(self, panchayat_id: str) -> list[WaterSource]
```

All functional (`is_functional=True`) sources for a panchayat.

#### `total_supply_lpd`

```python
def total_supply_lpd(self, panchayat_id: str) -> float
```

Sum of `current_yield_lpd` for all functional sources in a panchayat.

#### `low_yield_sources`

```python
def low_yield_sources(
    self,
    panchayat_id: str,
    threshold_pct: float = 40.0,
) -> list[WaterSource]
```

Functional sources whose `yield_pct` is below `threshold_pct`.

#### `non_functional_sources`

```python
def non_functional_sources(self, panchayat_id: str) -> list[WaterSource]
```

Sources with `is_functional=False`.

---

### `JJMTracker`

Track Jal Jeevan Mission FHTC coverage.

```python
class JJMTracker:
    def __init__(self) -> None: ...
```

**Methods:**

#### `update`

```python
def update(self, status: FHTCStatus) -> None
```

Add or overwrite FHTC status for a panchayat (keyed by `panchayat_id`).

#### `get`

```python
def get(self, panchayat_id: str) -> FHTCStatus | None
```

Get status by panchayat ID.

#### `all_statuses`

```python
def all_statuses(self) -> list[FHTCStatus]
```

Return all tracked panchayat statuses.

#### `coverage_summary`

```python
def coverage_summary(self) -> dict[str, float]
```

Return average coverage and functional percentages across all tracked panchayats.

Returns: `{"avg_coverage_pct": float, "avg_functional_pct": float}`.
Returns `0.0` values if no panchayats are tracked.

#### `below_target`

```python
def below_target(self, target_pct: float = 100.0) -> list[FHTCStatus]
```

Panchayats whose `coverage_pct` is below `target_pct`.

#### `demand_gap`

```python
def demand_gap(self, panchayat_id: str) -> int
```

Number of households not yet connected: `max(0, total_households - fhtc_provided)`.
Returns `0` if panchayat not found.

#### `lpcd_check`

```python
def lpcd_check(
    self,
    panchayat_id: str,
    population: int,
    total_supply_lpd: float,
) -> dict[str, float]
```

Check if water supply meets the JJM 55 LPCD standard.

Returns: `{"actual_lpcd": float, "required_lpcd": 55.0, "gap_lpd": float}`.

`gap_lpd` is the additional litres per day needed to reach the JJM standard (0 if already met).

---

### `GroundwaterMonitor`

Monitor groundwater levels across seasons.

```python
class GroundwaterMonitor:
    def __init__(self) -> None: ...
```

**Methods:**

#### `add`

```python
def add(self, record: GroundwaterLevel) -> None
```

Add a groundwater level record.

#### `by_panchayat`

```python
def by_panchayat(self, panchayat_id: str) -> list[GroundwaterLevel]
```

All records for a panchayat, sorted by `(year, season.value)`.

#### `latest`

```python
def latest(self, panchayat_id: str) -> GroundwaterLevel | None
```

Most recent record for a panchayat (last in sorted order). Returns `None` if no records.

#### `declining_trend`

```python
def declining_trend(self, panchayat_id: str, years: int = 3) -> bool
```

Check if groundwater has been declining for consecutive years.

Filters to `PRE_MONSOON` records only, sorted by year. Takes the most recent `years`
records. Returns `True` only if every consecutive pair shows increasing depth.
Returns `False` if fewer than 2 records are available.

#### `categorize_level`

```python
def categorize_level(self, depth_meters: float) -> str
```

Categorise groundwater depth per CGWB standards.

| Depth range | Return value |
|-------------|-------------|
| < 2m | `"very_shallow"` |
| 2–8m | `"shallow"` |
| 8–20m | `"moderate"` |
| 20–40m | `"deep"` |
| > 40m | `"very_deep"` |

#### `recharge_potential`

```python
def recharge_potential(self, panchayat_id: str) -> str
```

Estimate monsoon recharge potential from `PRE_MONSOON` vs `POST_MONSOON` depth difference
in the same year.

Returns: `"high"` (> 5m recovery), `"moderate"` (2–5m), `"low"` (0–2m),
`"negligible"` (<= 0), or `"insufficient_data"` if matching records unavailable.

---

### `RainfallAnalyzer`

Analyse rainfall patterns for drought/flood risk.

```python
class RainfallAnalyzer:
    def __init__(self) -> None: ...
```

**Methods:**

#### `add`

```python
def add(self, record: RainfallRecord) -> None
```

Add a monthly rainfall record.

#### `annual_total`

```python
def annual_total(self, panchayat_id: str, year: int) -> float
```

Sum of `rainfall_mm` for all months in the given panchayat and year.

#### `annual_normal`

```python
def annual_normal(self, panchayat_id: str, year: int) -> float
```

Sum of `normal_mm` for all months in the given panchayat and year.

#### `annual_deviation_pct`

```python
def annual_deviation_pct(self, panchayat_id: str, year: int) -> float
```

Percentage deviation of annual total from annual normal.
Returns `0.0` if no normal data.

#### `drought_risk`

```python
def drought_risk(self, panchayat_id: str, year: int) -> str
```

IMD drought classification based on annual rainfall deviation.

| Deviation | Classification |
|-----------|----------------|
| <= -60% | `"severe_drought"` |
| <= -40% | `"moderate_drought"` |
| <= -20% | `"mild_drought"` |
| > -20% | `"normal"` |

#### `flood_risk`

```python
def flood_risk(self, panchayat_id: str, year: int) -> str
```

Flood risk based on excess annual rainfall.

| Deviation | Classification |
|-----------|----------------|
| >= 60% | `"high_flood_risk"` |
| >= 30% | `"moderate_flood_risk"` |
| < 30% | `"normal"` |

#### `monsoon_performance`

```python
def monsoon_performance(self, panchayat_id: str, year: int) -> dict[str, float]
```

June–September rainfall vs climatological normal.

Returns: `{"actual_mm": float, "normal_mm": float, "deviation_pct": float}`.

---

### `WaterBudgetPlanner`

Plan water budgets for panchayats.

```python
class WaterBudgetPlanner:
    DOMESTIC_LPCD: int = 55
    LIVESTOCK_LPCD: int = 30
    IRRIGATION_MM_PER_HECTARE: int = 500
```

**Class attributes:**

| Attribute | Value | Description |
|-----------|-------|-------------|
| `DOMESTIC_LPCD` | 55 | JJM per-capita daily target |
| `LIVESTOCK_LPCD` | 30 | Per large animal equivalent daily demand |
| `IRRIGATION_MM_PER_HECTARE` | 500 | Average annual irrigation depth in mm |

**Methods:**

#### `estimate_demand`

```python
def estimate_demand(
    self,
    population: int,
    livestock: int = 0,
    irrigated_hectares: float = 0,
) -> WaterBudget
```

Estimate daily water demand breakdown.

| Parameter | Type | Description |
|-----------|------|-------------|
| `population` | `int` | Village population |
| `livestock` | `int` | Number of large livestock |
| `irrigated_hectares` | `float` | Irrigated area in hectares |

Returns: `WaterBudget` with `panchayat_id=""`, `year=0`, `total_supply_lpd=0`,
`industrial_demand_lpd=0`. Set `total_supply_lpd` separately before calling
`sustainability_index`.

Demand calculations:
- `domestic_demand_lpd = population * DOMESTIC_LPCD`
- `agriculture_demand_lpd = irrigated_hectares * 500_000 / 365 + livestock * LIVESTOCK_LPCD`
- `total_demand_lpd = domestic + agriculture`

#### `sustainability_index`

```python
def sustainability_index(self, budget: WaterBudget) -> float
```

0–100 sustainability score where 100 = fully sustainable.

Formula: `min(100.0, (total_supply_lpd / total_demand_lpd) * 100)`.
Returns `100.0` if `total_demand_lpd == 0`.

---

### `AlertEngine`

Generate water-related alerts.

```python
class AlertEngine:
    def __init__(self) -> None: ...
```

Alert IDs are sequential within an `AlertEngine` instance: `"ALERT-0001"`, `"ALERT-0002"`, etc.

**Methods:**

#### `check_quality`

```python
def check_quality(self, report: WaterQualityReport) -> list[WaterAlert]
```

Generate alerts based on water quality grade.

| Grade | Alert level | Alert category |
|-------|-------------|----------------|
| `HAZARDOUS` | `EMERGENCY` | `"water_quality"` |
| `CONTAMINATED` | `WARNING` | `"water_quality"` |
| `SAFE` or `ACCEPTABLE` | — | No alert |

#### `check_groundwater`

```python
def check_groundwater(self, record: GroundwaterLevel) -> list[WaterAlert]
```

Generate alerts based on groundwater depth and trend.

| Condition | Level | Category |
|-----------|-------|----------|
| depth > 40m | `CRITICAL` | `"groundwater"` |
| depth 20–40m | `WARNING` | `"groundwater"` |
| `is_declining` and `change_meters > 2` | `WARNING` | `"groundwater_trend"` |

May return 0, 1, or 2 alerts per record.

#### `check_supply`

```python
def check_supply(
    self,
    population: int,
    total_supply_lpd: float,
) -> list[WaterAlert]
```

Generate alerts if supply LPCD is below JJM standard.

| Condition | Level | Category |
|-----------|-------|----------|
| LPCD < 27 (half of 55) | `EMERGENCY` | `"supply"` |
| 27 <= LPCD < 55 | `WARNING` | `"supply"` |
| LPCD >= 55 | — | No alert |

Returns empty list if `population == 0`.

#### `check_rainfall`

```python
def check_rainfall(
    self,
    panchayat_id: str,
    deviation_pct: float,
) -> list[WaterAlert]
```

Generate drought or flood alerts based on rainfall deviation.

| Condition | Level | Category |
|-----------|-------|----------|
| deviation <= -40% | `CRITICAL` | `"drought"` |
| deviation >= +60% | `CRITICAL` | `"flood"` |
| otherwise | — | No alert |

---

## Public API Surface (`__all__`)

### `aumai_jaldrishti` (package `__init__`)

```python
__all__ = [
    "AlertEngine", "AlertLevel", "FHTCStatus",
    "GroundwaterLevel", "GroundwaterMonitor",
    "JJMTracker", "RainfallAnalyzer", "RainfallRecord",
    "SeasonType", "SourceManager",
    "WaterAlert", "WaterBudget", "WaterBudgetPlanner",
    "WaterQualityAnalyzer", "WaterQualityGrade",
    "WaterQualityReport", "WaterSource", "WaterSourceType",
]
```

### `aumai_jaldrishti.core`

```python
__all__ = [
    "WaterQualityAnalyzer", "SourceManager", "JJMTracker",
    "GroundwaterMonitor", "RainfallAnalyzer",
    "WaterBudgetPlanner", "AlertEngine",
]
```

### `aumai_jaldrishti.models`

```python
__all__ = [
    "WaterSourceType", "WaterQualityGrade", "SeasonType", "AlertLevel",
    "WaterSource", "WaterQualityReport", "FHTCStatus", "GroundwaterLevel",
    "WaterAlert", "WaterBudget", "RainfallRecord",
]
```

---

## Exceptions

| Situation | Exception |
|-----------|-----------|
| Invalid field values | `pydantic.ValidationError` |
| File not found (CLI) | Click exits with error message |
| Invalid JSON (CLI) | `json.JSONDecodeError` |

No custom exception classes are defined.
