"""Core logic for aumai-jaldrishti."""

from __future__ import annotations

from aumai_jaldrishti.models import (
    AlertLevel,
    FHTCStatus,
    GroundwaterLevel,
    RainfallRecord,
    SeasonType,
    WaterAlert,
    WaterBudget,
    WaterQualityGrade,
    WaterQualityReport,
    WaterSource,
    WaterSourceType,
)

_DISCLAIMER = "Verify water quality data with local authorities before consumption decisions."

# BIS 10500:2012 drinking water standards
_BIS_LIMITS = {
    "ph_min": 6.5,
    "ph_max": 8.5,
    "tds_acceptable": 500,
    "tds_permissible": 2000,
    "turbidity_acceptable": 1,
    "turbidity_permissible": 5,
    "chloride_acceptable": 250,
    "chloride_permissible": 1000,
    "fluoride_acceptable": 1.0,
    "fluoride_permissible": 1.5,
    "arsenic_max_ppb": 10,
    "iron_acceptable": 0.3,
    "iron_permissible": 1.0,
    "nitrate_max": 45,
}

# LPCD = liters per capita per day (Jal Jeevan Mission standard: 55 LPCD)
JJM_LPCD_STANDARD = 55


__all__ = [
    "WaterQualityAnalyzer",
    "SourceManager",
    "JJMTracker",
    "GroundwaterMonitor",
    "RainfallAnalyzer",
    "WaterBudgetPlanner",
    "AlertEngine",
]


class WaterQualityAnalyzer:
    """Analyze water quality against BIS 10500:2012 standards."""

    def grade_report(self, report: WaterQualityReport) -> WaterQualityGrade:
        """Assign quality grade based on BIS limits."""
        hazardous = False
        contaminated = False

        # pH
        if report.ph < 5.0 or report.ph > 9.5:
            hazardous = True
        elif report.ph < _BIS_LIMITS["ph_min"] or report.ph > _BIS_LIMITS["ph_max"]:
            contaminated = True

        # TDS
        if report.tds_ppm > _BIS_LIMITS["tds_permissible"]:
            hazardous = True
        elif report.tds_ppm > _BIS_LIMITS["tds_acceptable"]:
            contaminated = True

        # Turbidity
        if report.turbidity_ntu > _BIS_LIMITS["turbidity_permissible"]:
            contaminated = True

        # Fluoride
        if report.fluoride_ppm > _BIS_LIMITS["fluoride_permissible"]:
            hazardous = True
        elif report.fluoride_ppm > _BIS_LIMITS["fluoride_acceptable"]:
            contaminated = True

        # Arsenic
        if report.arsenic_ppb > _BIS_LIMITS["arsenic_max_ppb"]:
            hazardous = True

        # Iron
        if report.iron_ppm > _BIS_LIMITS["iron_permissible"]:
            contaminated = True

        # Nitrate
        if report.nitrate_ppm > _BIS_LIMITS["nitrate_max"]:
            hazardous = True

        # Coliform
        if report.coliform_present:
            hazardous = True

        if hazardous:
            return WaterQualityGrade.HAZARDOUS
        if contaminated:
            return WaterQualityGrade.CONTAMINATED
        # Check if all within acceptable (not just permissible)
        if (
            report.tds_ppm <= _BIS_LIMITS["tds_acceptable"]
            and report.turbidity_ntu <= _BIS_LIMITS["turbidity_acceptable"]
            and report.fluoride_ppm <= _BIS_LIMITS["fluoride_acceptable"]
            and report.iron_ppm <= _BIS_LIMITS["iron_acceptable"]
        ):
            return WaterQualityGrade.SAFE
        return WaterQualityGrade.ACCEPTABLE

    def identify_contaminants(self, report: WaterQualityReport) -> list[str]:
        """List parameters exceeding BIS acceptable limits."""
        issues: list[str] = []
        if report.ph < _BIS_LIMITS["ph_min"]:
            issues.append(f"pH too low: {report.ph} (min {_BIS_LIMITS['ph_min']})")
        if report.ph > _BIS_LIMITS["ph_max"]:
            issues.append(f"pH too high: {report.ph} (max {_BIS_LIMITS['ph_max']})")
        if report.tds_ppm > _BIS_LIMITS["tds_acceptable"]:
            issues.append(f"TDS: {report.tds_ppm} ppm (limit {_BIS_LIMITS['tds_acceptable']})")
        if report.turbidity_ntu > _BIS_LIMITS["turbidity_acceptable"]:
            issues.append(f"Turbidity: {report.turbidity_ntu} NTU (limit {_BIS_LIMITS['turbidity_acceptable']})")
        if report.fluoride_ppm > _BIS_LIMITS["fluoride_acceptable"]:
            issues.append(f"Fluoride: {report.fluoride_ppm} ppm (limit {_BIS_LIMITS['fluoride_acceptable']})")
        if report.arsenic_ppb > _BIS_LIMITS["arsenic_max_ppb"]:
            issues.append(f"Arsenic: {report.arsenic_ppb} ppb (limit {_BIS_LIMITS['arsenic_max_ppb']})")
        if report.iron_ppm > _BIS_LIMITS["iron_acceptable"]:
            issues.append(f"Iron: {report.iron_ppm} ppm (limit {_BIS_LIMITS['iron_acceptable']})")
        if report.nitrate_ppm > _BIS_LIMITS["nitrate_max"]:
            issues.append(f"Nitrate: {report.nitrate_ppm} ppm (limit {_BIS_LIMITS['nitrate_max']})")
        if report.chloride_ppm > _BIS_LIMITS["chloride_acceptable"]:
            issues.append(f"Chloride: {report.chloride_ppm} ppm (limit {_BIS_LIMITS['chloride_acceptable']})")
        if report.coliform_present:
            issues.append("Coliform bacteria detected")
        return issues

    def recommend_treatment(self, report: WaterQualityReport) -> list[str]:
        """Suggest treatment based on contaminants found."""
        treatments: list[str] = []
        if report.coliform_present:
            treatments.append("Chlorination or UV disinfection for bacterial contamination")
        if report.tds_ppm > _BIS_LIMITS["tds_acceptable"]:
            treatments.append("Reverse osmosis (RO) for high TDS")
        if report.fluoride_ppm > _BIS_LIMITS["fluoride_acceptable"]:
            treatments.append("Activated alumina or bone char defluoridation")
        if report.arsenic_ppb > _BIS_LIMITS["arsenic_max_ppb"]:
            treatments.append("Arsenic removal plant (oxidation + adsorption)")
        if report.iron_ppm > _BIS_LIMITS["iron_acceptable"]:
            treatments.append("Aeration and filtration for iron removal")
        if report.turbidity_ntu > _BIS_LIMITS["turbidity_acceptable"]:
            treatments.append("Slow sand filtration or coagulation-flocculation")
        if report.nitrate_ppm > _BIS_LIMITS["nitrate_max"]:
            treatments.append("Ion exchange or biological denitrification")
        if report.ph < _BIS_LIMITS["ph_min"]:
            treatments.append("Lime dosing to raise pH")
        if report.ph > _BIS_LIMITS["ph_max"]:
            treatments.append("Acid dosing or CO2 injection to lower pH")
        return treatments


class SourceManager:
    """Manage and monitor water sources for a panchayat."""

    def __init__(self) -> None:
        self._sources: dict[str, WaterSource] = {}

    def register(self, source: WaterSource) -> None:
        self._sources[source.source_id] = source

    def get(self, source_id: str) -> WaterSource | None:
        return self._sources.get(source_id)

    def by_panchayat(self, panchayat_id: str) -> list[WaterSource]:
        return [s for s in self._sources.values() if s.panchayat_id == panchayat_id]

    def by_type(self, source_type: WaterSourceType) -> list[WaterSource]:
        return [s for s in self._sources.values() if s.source_type == source_type]

    def functional_sources(self, panchayat_id: str) -> list[WaterSource]:
        return [s for s in self.by_panchayat(panchayat_id) if s.is_functional]

    def total_supply_lpd(self, panchayat_id: str) -> float:
        return sum(s.current_yield_lpd for s in self.functional_sources(panchayat_id))

    def low_yield_sources(self, panchayat_id: str, threshold_pct: float = 40.0) -> list[WaterSource]:
        return [s for s in self.functional_sources(panchayat_id) if s.yield_pct < threshold_pct]

    def non_functional_sources(self, panchayat_id: str) -> list[WaterSource]:
        return [s for s in self.by_panchayat(panchayat_id) if not s.is_functional]


class JJMTracker:
    """Track Jal Jeevan Mission FHTC coverage."""

    def __init__(self) -> None:
        self._records: dict[str, FHTCStatus] = {}

    def update(self, status: FHTCStatus) -> None:
        self._records[status.panchayat_id] = status

    def get(self, panchayat_id: str) -> FHTCStatus | None:
        return self._records.get(panchayat_id)

    def all_statuses(self) -> list[FHTCStatus]:
        return list(self._records.values())

    def coverage_summary(self) -> dict[str, float]:
        """Return average coverage and functional percentages."""
        if not self._records:
            return {"avg_coverage_pct": 0.0, "avg_functional_pct": 0.0}
        coverages = [s.coverage_pct for s in self._records.values()]
        functionals = [s.functional_pct for s in self._records.values() if s.fhtc_provided > 0]
        return {
            "avg_coverage_pct": round(sum(coverages) / len(coverages), 1),
            "avg_functional_pct": round(sum(functionals) / len(functionals), 1) if functionals else 0.0,
        }

    def below_target(self, target_pct: float = 100.0) -> list[FHTCStatus]:
        return [s for s in self._records.values() if s.coverage_pct < target_pct]

    def demand_gap(self, panchayat_id: str) -> int:
        status = self._records.get(panchayat_id)
        if status is None:
            return 0
        return max(0, status.total_households - status.fhtc_provided)

    def lpcd_check(self, panchayat_id: str, population: int, total_supply_lpd: float) -> dict[str, float]:
        """Check if LPCD meets JJM standard of 55 LPCD."""
        if population == 0:
            return {"actual_lpcd": 0.0, "required_lpcd": float(JJM_LPCD_STANDARD), "gap_lpd": 0.0}
        actual_lpcd = total_supply_lpd / population
        required_lpd = population * JJM_LPCD_STANDARD
        gap_lpd = max(0.0, required_lpd - total_supply_lpd)
        return {
            "actual_lpcd": round(actual_lpcd, 1),
            "required_lpcd": float(JJM_LPCD_STANDARD),
            "gap_lpd": round(gap_lpd, 0),
        }


class GroundwaterMonitor:
    """Monitor groundwater levels across seasons."""

    def __init__(self) -> None:
        self._records: list[GroundwaterLevel] = []

    def add(self, record: GroundwaterLevel) -> None:
        self._records.append(record)

    def by_panchayat(self, panchayat_id: str) -> list[GroundwaterLevel]:
        return sorted(
            [r for r in self._records if r.panchayat_id == panchayat_id],
            key=lambda r: (r.year, r.season.value),
        )

    def latest(self, panchayat_id: str) -> GroundwaterLevel | None:
        records = self.by_panchayat(panchayat_id)
        return records[-1] if records else None

    def declining_trend(self, panchayat_id: str, years: int = 3) -> bool:
        """Check if groundwater has been declining for consecutive years."""
        records = [r for r in self._records if r.panchayat_id == panchayat_id and r.season == SeasonType.PRE_MONSOON]
        records.sort(key=lambda r: r.year)
        recent = records[-years:] if len(records) >= years else records
        if len(recent) < 2:
            return False
        return all(recent[i].depth_meters > recent[i - 1].depth_meters for i in range(1, len(recent)))

    def categorize_level(self, depth_meters: float) -> str:
        """Categorize groundwater level per CGWB standards."""
        if depth_meters < 2:
            return "very_shallow"
        if depth_meters < 8:
            return "shallow"
        if depth_meters < 20:
            return "moderate"
        if depth_meters < 40:
            return "deep"
        return "very_deep"

    def recharge_potential(self, panchayat_id: str) -> str:
        """Estimate recharge potential from monsoon recovery."""
        records = [r for r in self._records if r.panchayat_id == panchayat_id]
        pre = [r for r in records if r.season == SeasonType.PRE_MONSOON]
        post = [r for r in records if r.season == SeasonType.POST_MONSOON]
        if not pre or not post:
            return "insufficient_data"
        latest_pre = max(pre, key=lambda r: r.year)
        latest_post = max(post, key=lambda r: r.year)
        if latest_pre.year != latest_post.year:
            return "insufficient_data"
        recovery = latest_pre.depth_meters - latest_post.depth_meters
        if recovery > 5:
            return "high"
        if recovery > 2:
            return "moderate"
        if recovery > 0:
            return "low"
        return "negligible"


class RainfallAnalyzer:
    """Analyze rainfall patterns for drought/flood risk."""

    def __init__(self) -> None:
        self._records: list[RainfallRecord] = []

    def add(self, record: RainfallRecord) -> None:
        self._records.append(record)

    def annual_total(self, panchayat_id: str, year: int) -> float:
        return sum(r.rainfall_mm for r in self._records if r.panchayat_id == panchayat_id and r.year == year)

    def annual_normal(self, panchayat_id: str, year: int) -> float:
        return sum(r.normal_mm for r in self._records if r.panchayat_id == panchayat_id and r.year == year)

    def annual_deviation_pct(self, panchayat_id: str, year: int) -> float:
        normal = self.annual_normal(panchayat_id, year)
        if normal == 0:
            return 0.0
        actual = self.annual_total(panchayat_id, year)
        return round(((actual - normal) / normal) * 100, 1)

    def drought_risk(self, panchayat_id: str, year: int) -> str:
        """IMD drought classification based on rainfall deviation."""
        dev = self.annual_deviation_pct(panchayat_id, year)
        if dev <= -60:
            return "severe_drought"
        if dev <= -40:
            return "moderate_drought"
        if dev <= -20:
            return "mild_drought"
        return "normal"

    def flood_risk(self, panchayat_id: str, year: int) -> str:
        """Simple flood risk based on excess rainfall."""
        dev = self.annual_deviation_pct(panchayat_id, year)
        if dev >= 60:
            return "high_flood_risk"
        if dev >= 30:
            return "moderate_flood_risk"
        return "normal"

    def monsoon_performance(self, panchayat_id: str, year: int) -> dict[str, float]:
        """June-September rainfall vs normal."""
        monsoon_months = {6, 7, 8, 9}
        records = [r for r in self._records if r.panchayat_id == panchayat_id and r.year == year and r.month in monsoon_months]
        actual = sum(r.rainfall_mm for r in records)
        normal = sum(r.normal_mm for r in records)
        deviation = ((actual - normal) / normal * 100) if normal > 0 else 0.0
        return {"actual_mm": round(actual, 1), "normal_mm": round(normal, 1), "deviation_pct": round(deviation, 1)}


class WaterBudgetPlanner:
    """Plan water budgets for panchayats."""

    DOMESTIC_LPCD = 55  # JJM standard
    LIVESTOCK_LPCD = 30  # per large animal equivalent
    IRRIGATION_MM_PER_HECTARE = 500  # average seasonal

    def estimate_demand(self, population: int, livestock: int = 0, irrigated_hectares: float = 0) -> WaterBudget:
        """Estimate daily water demand breakdown."""
        domestic = population * self.DOMESTIC_LPCD
        agriculture = irrigated_hectares * self.IRRIGATION_MM_PER_HECTARE * 1000 / 365  # convert annual to daily
        livestock_demand = livestock * self.LIVESTOCK_LPCD
        return WaterBudget(
            panchayat_id="",
            year=0,
            total_demand_lpd=round(domestic + agriculture + livestock_demand, 0),
            total_supply_lpd=0,
            domestic_demand_lpd=round(domestic, 0),
            agriculture_demand_lpd=round(agriculture + livestock_demand, 0),
            industrial_demand_lpd=0,
        )

    def sustainability_index(self, budget: WaterBudget) -> float:
        """0-100 index where 100 = fully sustainable."""
        if budget.total_demand_lpd == 0:
            return 100.0
        ratio = budget.total_supply_lpd / budget.total_demand_lpd
        return round(min(100.0, ratio * 100), 1)


class AlertEngine:
    """Generate water-related alerts."""

    def __init__(self) -> None:
        self._alert_counter = 0

    def _next_id(self) -> str:
        self._alert_counter += 1
        return f"ALERT-{self._alert_counter:04d}"

    def check_quality(self, report: WaterQualityReport) -> list[WaterAlert]:
        analyzer = WaterQualityAnalyzer()
        grade = analyzer.grade_report(report)
        alerts: list[WaterAlert] = []
        if grade == WaterQualityGrade.HAZARDOUS:
            alerts.append(WaterAlert(
                alert_id=self._next_id(), panchayat_id="", level=AlertLevel.EMERGENCY,
                category="water_quality", message=f"HAZARDOUS water quality at source {report.source_id}. Do NOT consume.",
                source_id=report.source_id, date=report.test_date,
            ))
        elif grade == WaterQualityGrade.CONTAMINATED:
            alerts.append(WaterAlert(
                alert_id=self._next_id(), panchayat_id="", level=AlertLevel.WARNING,
                category="water_quality", message=f"Contaminated water at source {report.source_id}. Treatment required.",
                source_id=report.source_id, date=report.test_date,
            ))
        return alerts

    def check_groundwater(self, record: GroundwaterLevel) -> list[WaterAlert]:
        alerts: list[WaterAlert] = []
        if record.depth_meters > 40:
            alerts.append(WaterAlert(
                alert_id=self._next_id(), panchayat_id=record.panchayat_id, level=AlertLevel.CRITICAL,
                category="groundwater", message=f"Groundwater critically deep: {record.depth_meters}m. Immediate conservation needed.",
            ))
        elif record.depth_meters > 20:
            alerts.append(WaterAlert(
                alert_id=self._next_id(), panchayat_id=record.panchayat_id, level=AlertLevel.WARNING,
                category="groundwater", message=f"Groundwater declining: {record.depth_meters}m depth.",
            ))
        if record.is_declining and record.change_meters > 2:
            alerts.append(WaterAlert(
                alert_id=self._next_id(), panchayat_id=record.panchayat_id, level=AlertLevel.WARNING,
                category="groundwater_trend", message=f"Groundwater dropped {record.change_meters}m from last year.",
            ))
        return alerts

    def check_supply(self, population: int, total_supply_lpd: float) -> list[WaterAlert]:
        alerts: list[WaterAlert] = []
        if population == 0:
            return alerts
        lpcd = total_supply_lpd / population
        if lpcd < 27:  # Half of JJM standard
            alerts.append(WaterAlert(
                alert_id=self._next_id(), panchayat_id="", level=AlertLevel.EMERGENCY,
                category="supply", message=f"Severe water scarcity: only {lpcd:.0f} LPCD (need {JJM_LPCD_STANDARD}).",
            ))
        elif lpcd < JJM_LPCD_STANDARD:
            alerts.append(WaterAlert(
                alert_id=self._next_id(), panchayat_id="", level=AlertLevel.WARNING,
                category="supply", message=f"Water supply below JJM standard: {lpcd:.0f} LPCD (need {JJM_LPCD_STANDARD}).",
            ))
        return alerts

    def check_rainfall(self, panchayat_id: str, deviation_pct: float) -> list[WaterAlert]:
        alerts: list[WaterAlert] = []
        if deviation_pct <= -40:
            alerts.append(WaterAlert(
                alert_id=self._next_id(), panchayat_id=panchayat_id, level=AlertLevel.CRITICAL,
                category="drought", message=f"Drought conditions: rainfall {deviation_pct:.0f}% below normal.",
            ))
        elif deviation_pct >= 60:
            alerts.append(WaterAlert(
                alert_id=self._next_id(), panchayat_id=panchayat_id, level=AlertLevel.CRITICAL,
                category="flood", message=f"Flood risk: rainfall {deviation_pct:.0f}% above normal.",
            ))
        return alerts
