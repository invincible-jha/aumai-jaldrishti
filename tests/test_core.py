"""Comprehensive tests for aumai-jaldrishti core module.

Covers:
- WaterQualityAnalyzer
- SourceManager
- JJMTracker
- GroundwaterMonitor
- RainfallAnalyzer
- WaterBudgetPlanner
- AlertEngine
- All models
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aumai_jaldrishti.core import (
    AlertEngine,
    GroundwaterMonitor,
    JJMTracker,
    RainfallAnalyzer,
    SourceManager,
    WaterBudgetPlanner,
    WaterQualityAnalyzer,
)
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


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def make_clean_report(
    report_id: str = "RPT001",
    source_id: str = "SRC001",
    test_date: str = "2025-01-15",
) -> WaterQualityReport:
    """Create a fully safe quality report within BIS acceptable limits."""
    return WaterQualityReport(
        report_id=report_id,
        source_id=source_id,
        test_date=test_date,
        ph=7.0,
        tds_ppm=300.0,
        turbidity_ntu=0.5,
        chloride_ppm=100.0,
        fluoride_ppm=0.5,
        arsenic_ppb=2.0,
        iron_ppm=0.1,
        nitrate_ppm=20.0,
        coliform_present=False,
    )


def make_source(
    source_id: str = "SRC001",
    panchayat_id: str = "GP001",
    name: str = "Main Borewell",
    source_type: WaterSourceType = WaterSourceType.BOREWELL,
    capacity_liters_per_day: float = 10000.0,
    current_yield_lpd: float = 7000.0,
    is_functional: bool = True,
) -> WaterSource:
    return WaterSource(
        source_id=source_id,
        panchayat_id=panchayat_id,
        name=name,
        source_type=source_type,
        latitude=26.9,
        longitude=80.9,
        capacity_liters_per_day=capacity_liters_per_day,
        current_yield_lpd=current_yield_lpd,
        is_functional=is_functional,
    )


def make_fhtc_status(
    panchayat_id: str = "GP001",
    panchayat_name: str = "Rampur",
    total_households: int = 500,
    fhtc_provided: int = 400,
    fhtc_functional: int = 350,
) -> FHTCStatus:
    return FHTCStatus(
        panchayat_id=panchayat_id,
        panchayat_name=panchayat_name,
        total_households=total_households,
        fhtc_provided=fhtc_provided,
        fhtc_functional=fhtc_functional,
    )


def make_groundwater_record(
    panchayat_id: str = "GP001",
    season: SeasonType = SeasonType.PRE_MONSOON,
    year: int = 2024,
    depth_meters: float = 10.0,
    previous_year_depth: float = 8.0,
) -> GroundwaterLevel:
    return GroundwaterLevel(
        panchayat_id=panchayat_id,
        season=season,
        year=year,
        depth_meters=depth_meters,
        previous_year_depth=previous_year_depth,
    )


def make_rainfall_record(
    panchayat_id: str = "GP001",
    month: int = 7,
    year: int = 2024,
    rainfall_mm: float = 200.0,
    normal_mm: float = 180.0,
) -> RainfallRecord:
    return RainfallRecord(
        panchayat_id=panchayat_id,
        month=month,
        year=year,
        rainfall_mm=rainfall_mm,
        normal_mm=normal_mm,
    )


# ---------------------------------------------------------------------------
# WaterSource model tests
# ---------------------------------------------------------------------------


class TestWaterSourceModel:
    def test_yield_pct_calculation(self) -> None:
        source = make_source(capacity_liters_per_day=10000.0, current_yield_lpd=7000.0)
        assert source.yield_pct == 70.0

    def test_yield_pct_zero_capacity(self) -> None:
        source = WaterSource(
            source_id="S1",
            panchayat_id="GP001",
            name="Test",
            source_type=WaterSourceType.HANDPUMP,
            latitude=0.0,
            longitude=0.0,
            capacity_liters_per_day=0.0,
            current_yield_lpd=0.0,
        )
        assert source.yield_pct == 0.0

    def test_latitude_bounds(self) -> None:
        with pytest.raises(ValidationError):
            WaterSource(
                source_id="S1",
                panchayat_id="GP001",
                name="Test",
                source_type=WaterSourceType.BOREWELL,
                latitude=91.0,
                longitude=0.0,
                capacity_liters_per_day=1000.0,
                current_yield_lpd=500.0,
            )

    def test_longitude_bounds(self) -> None:
        with pytest.raises(ValidationError):
            WaterSource(
                source_id="S1",
                panchayat_id="GP001",
                name="Test",
                source_type=WaterSourceType.BOREWELL,
                latitude=0.0,
                longitude=181.0,
                capacity_liters_per_day=1000.0,
                current_yield_lpd=500.0,
            )

    def test_is_functional_defaults_true(self) -> None:
        source = make_source()
        assert source.is_functional is True


# ---------------------------------------------------------------------------
# FHTCStatus model tests
# ---------------------------------------------------------------------------


class TestFHTCStatusModel:
    def test_coverage_pct(self) -> None:
        status = make_fhtc_status(total_households=500, fhtc_provided=400)
        assert status.coverage_pct == 80.0

    def test_coverage_pct_zero_households(self) -> None:
        status = FHTCStatus(
            panchayat_id="GP001",
            panchayat_name="Test",
            total_households=0,
            fhtc_provided=0,
            fhtc_functional=0,
        )
        assert status.coverage_pct == 0.0

    def test_functional_pct(self) -> None:
        status = make_fhtc_status(fhtc_provided=400, fhtc_functional=320)
        assert status.functional_pct == 80.0

    def test_functional_pct_zero_provided(self) -> None:
        status = FHTCStatus(
            panchayat_id="GP001",
            panchayat_name="Test",
            total_households=500,
            fhtc_provided=0,
            fhtc_functional=0,
        )
        assert status.functional_pct == 0.0


# ---------------------------------------------------------------------------
# GroundwaterLevel model tests
# ---------------------------------------------------------------------------


class TestGroundwaterLevelModel:
    def test_change_meters_positive(self) -> None:
        record = make_groundwater_record(depth_meters=10.0, previous_year_depth=8.0)
        assert record.change_meters == 2.0

    def test_is_declining_true(self) -> None:
        record = make_groundwater_record(depth_meters=10.0, previous_year_depth=8.0)
        assert record.is_declining is True

    def test_is_declining_false(self) -> None:
        record = make_groundwater_record(depth_meters=6.0, previous_year_depth=8.0)
        assert record.is_declining is False

    def test_change_meters_negative(self) -> None:
        record = make_groundwater_record(depth_meters=5.0, previous_year_depth=8.0)
        assert record.change_meters == -3.0


# ---------------------------------------------------------------------------
# WaterBudget model tests
# ---------------------------------------------------------------------------


class TestWaterBudgetModel:
    def test_surplus_deficit_lpd_surplus(self) -> None:
        budget = WaterBudget(
            panchayat_id="GP001",
            year=2024,
            total_demand_lpd=10000.0,
            total_supply_lpd=12000.0,
            domestic_demand_lpd=8000.0,
            agriculture_demand_lpd=2000.0,
            industrial_demand_lpd=0.0,
        )
        assert budget.surplus_deficit_lpd == 2000.0

    def test_surplus_deficit_lpd_deficit(self) -> None:
        budget = WaterBudget(
            panchayat_id="GP001",
            year=2024,
            total_demand_lpd=15000.0,
            total_supply_lpd=10000.0,
            domestic_demand_lpd=12000.0,
            agriculture_demand_lpd=3000.0,
            industrial_demand_lpd=0.0,
        )
        assert budget.is_deficit is True

    def test_is_deficit_false_when_surplus(self) -> None:
        budget = WaterBudget(
            panchayat_id="GP001",
            year=2024,
            total_demand_lpd=10000.0,
            total_supply_lpd=12000.0,
            domestic_demand_lpd=8000.0,
            agriculture_demand_lpd=2000.0,
            industrial_demand_lpd=0.0,
        )
        assert budget.is_deficit is False


# ---------------------------------------------------------------------------
# RainfallRecord model tests
# ---------------------------------------------------------------------------


class TestRainfallRecordModel:
    def test_deviation_pct_above_normal(self) -> None:
        record = make_rainfall_record(rainfall_mm=200.0, normal_mm=160.0)
        assert record.deviation_pct == 25.0

    def test_deviation_pct_below_normal(self) -> None:
        record = make_rainfall_record(rainfall_mm=80.0, normal_mm=160.0)
        assert record.deviation_pct == -50.0

    def test_deviation_pct_zero_normal(self) -> None:
        record = RainfallRecord(panchayat_id="GP001", month=6, year=2024, rainfall_mm=100.0, normal_mm=0.0)
        assert record.deviation_pct == 0.0

    def test_month_bounds(self) -> None:
        with pytest.raises(ValidationError):
            RainfallRecord(panchayat_id="GP001", month=0, year=2024, rainfall_mm=100.0, normal_mm=90.0)
        with pytest.raises(ValidationError):
            RainfallRecord(panchayat_id="GP001", month=13, year=2024, rainfall_mm=100.0, normal_mm=90.0)


# ---------------------------------------------------------------------------
# WaterQualityAnalyzer tests
# ---------------------------------------------------------------------------


class TestWaterQualityAnalyzer:
    def test_grade_safe_report(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.SAFE

    def test_grade_hazardous_coliform(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.coliform_present = True
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.HAZARDOUS

    def test_grade_hazardous_high_ph(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.ph = 10.0  # Above 9.5
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.HAZARDOUS

    def test_grade_hazardous_low_ph(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.ph = 4.5  # Below 5.0
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.HAZARDOUS

    def test_grade_contaminated_high_tds(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.tds_ppm = 800.0  # Between 500 and 2000
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.CONTAMINATED

    def test_grade_hazardous_very_high_tds(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.tds_ppm = 2500.0  # Above 2000
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.HAZARDOUS

    def test_grade_hazardous_arsenic(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.arsenic_ppb = 15.0  # Above 10 ppb
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.HAZARDOUS

    def test_grade_hazardous_nitrate(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.nitrate_ppm = 50.0  # Above 45
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.HAZARDOUS

    def test_grade_hazardous_high_fluoride(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.fluoride_ppm = 2.0  # Above permissible 1.5
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.HAZARDOUS

    def test_grade_contaminated_borderline_ph(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.ph = 6.0  # Between 5.0 and 6.5 — below acceptable
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.CONTAMINATED

    def test_identify_contaminants_clean(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        issues = analyzer.identify_contaminants(report)
        assert issues == []

    def test_identify_contaminants_multiple(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.ph = 9.0  # high pH
        report.tds_ppm = 600.0  # high TDS
        report.coliform_present = True
        issues = analyzer.identify_contaminants(report)
        assert len(issues) >= 2
        assert any("pH too high" in issue for issue in issues)
        assert any("Coliform" in issue for issue in issues)

    def test_recommend_treatment_coliform(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.coliform_present = True
        treatments = analyzer.recommend_treatment(report)
        assert any("Chlorination" in t for t in treatments)

    def test_recommend_treatment_high_tds(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.tds_ppm = 700.0
        treatments = analyzer.recommend_treatment(report)
        assert any("RO" in t or "Reverse osmosis" in t for t in treatments)

    def test_recommend_treatment_fluoride(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.fluoride_ppm = 1.2
        treatments = analyzer.recommend_treatment(report)
        assert any("alumina" in t.lower() or "defluoridation" in t.lower() for t in treatments)

    def test_recommend_treatment_arsenic(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.arsenic_ppb = 15.0
        treatments = analyzer.recommend_treatment(report)
        assert any("Arsenic" in t for t in treatments)

    def test_recommend_treatment_iron(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.iron_ppm = 0.5
        treatments = analyzer.recommend_treatment(report)
        assert any("iron" in t.lower() or "Aeration" in t for t in treatments)

    def test_recommend_treatment_low_ph(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.ph = 6.0
        treatments = analyzer.recommend_treatment(report)
        assert any("pH" in t or "Lime" in t for t in treatments)

    def test_recommend_treatment_high_ph(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.ph = 9.0
        treatments = analyzer.recommend_treatment(report)
        assert any("pH" in t or "Acid" in t or "CO2" in t for t in treatments)

    def test_recommend_treatment_clean_water_empty(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        treatments = analyzer.recommend_treatment(report)
        assert treatments == []

    def test_grade_acceptable_between_acceptable_and_permissible(self) -> None:
        analyzer = WaterQualityAnalyzer()
        report = make_clean_report()
        report.iron_ppm = 0.5  # Between 0.3 (acceptable) and 1.0 (permissible)
        grade = analyzer.grade_report(report)
        assert grade == WaterQualityGrade.ACCEPTABLE


# ---------------------------------------------------------------------------
# SourceManager tests
# ---------------------------------------------------------------------------


class TestSourceManager:
    def test_register_and_get(self) -> None:
        manager = SourceManager()
        source = make_source()
        manager.register(source)
        retrieved = manager.get("SRC001")
        assert retrieved is not None
        assert retrieved.name == "Main Borewell"

    def test_get_nonexistent(self) -> None:
        manager = SourceManager()
        assert manager.get("NONEXISTENT") is None

    def test_by_panchayat(self) -> None:
        manager = SourceManager()
        manager.register(make_source(source_id="S1", panchayat_id="GP001"))
        manager.register(make_source(source_id="S2", panchayat_id="GP002"))
        result = manager.by_panchayat("GP001")
        assert len(result) == 1
        assert result[0].source_id == "S1"

    def test_by_type(self) -> None:
        manager = SourceManager()
        manager.register(make_source(source_id="S1", source_type=WaterSourceType.BOREWELL))
        manager.register(make_source(source_id="S2", source_type=WaterSourceType.HANDPUMP))
        result = manager.by_type(WaterSourceType.BOREWELL)
        assert len(result) == 1

    def test_functional_sources(self) -> None:
        manager = SourceManager()
        manager.register(make_source(source_id="S1", is_functional=True))
        manager.register(make_source(source_id="S2", is_functional=False))
        functional = manager.functional_sources("GP001")
        assert len(functional) == 1
        assert functional[0].source_id == "S1"

    def test_total_supply_lpd(self) -> None:
        manager = SourceManager()
        manager.register(make_source(source_id="S1", current_yield_lpd=5000.0))
        manager.register(make_source(source_id="S2", current_yield_lpd=3000.0))
        total = manager.total_supply_lpd("GP001")
        assert total == 8000.0

    def test_total_supply_excludes_non_functional(self) -> None:
        manager = SourceManager()
        manager.register(make_source(source_id="S1", current_yield_lpd=5000.0, is_functional=True))
        manager.register(make_source(source_id="S2", current_yield_lpd=3000.0, is_functional=False))
        total = manager.total_supply_lpd("GP001")
        assert total == 5000.0

    def test_low_yield_sources(self) -> None:
        manager = SourceManager()
        # 30% yield - below 40% threshold
        manager.register(make_source(source_id="S1", capacity_liters_per_day=10000, current_yield_lpd=3000))
        # 70% yield - above threshold
        manager.register(make_source(source_id="S2", capacity_liters_per_day=10000, current_yield_lpd=7000))
        low = manager.low_yield_sources("GP001")
        assert len(low) == 1
        assert low[0].source_id == "S1"

    def test_non_functional_sources(self) -> None:
        manager = SourceManager()
        manager.register(make_source(source_id="S1", is_functional=True))
        manager.register(make_source(source_id="S2", is_functional=False))
        non_functional = manager.non_functional_sources("GP001")
        assert len(non_functional) == 1
        assert non_functional[0].source_id == "S2"


# ---------------------------------------------------------------------------
# JJMTracker tests
# ---------------------------------------------------------------------------


class TestJJMTracker:
    def test_update_and_get(self) -> None:
        tracker = JJMTracker()
        status = make_fhtc_status()
        tracker.update(status)
        retrieved = tracker.get("GP001")
        assert retrieved is not None
        assert retrieved.panchayat_name == "Rampur"

    def test_get_nonexistent(self) -> None:
        tracker = JJMTracker()
        assert tracker.get("NONEXISTENT") is None

    def test_all_statuses(self) -> None:
        tracker = JJMTracker()
        tracker.update(make_fhtc_status(panchayat_id="GP001"))
        tracker.update(FHTCStatus(panchayat_id="GP002", panchayat_name="Shyampur", total_households=300, fhtc_provided=200, fhtc_functional=180))
        assert len(tracker.all_statuses()) == 2

    def test_coverage_summary_empty(self) -> None:
        tracker = JJMTracker()
        summary = tracker.coverage_summary()
        assert summary["avg_coverage_pct"] == 0.0
        assert summary["avg_functional_pct"] == 0.0

    def test_coverage_summary_with_data(self) -> None:
        tracker = JJMTracker()
        tracker.update(make_fhtc_status(total_households=500, fhtc_provided=400, fhtc_functional=360))
        summary = tracker.coverage_summary()
        assert summary["avg_coverage_pct"] == 80.0

    def test_below_target(self) -> None:
        tracker = JJMTracker()
        tracker.update(make_fhtc_status(panchayat_id="GP001", total_households=500, fhtc_provided=400))
        tracker.update(FHTCStatus(panchayat_id="GP002", panchayat_name="Full", total_households=300, fhtc_provided=300, fhtc_functional=300))
        below = tracker.below_target(100.0)
        assert any(s.panchayat_id == "GP001" for s in below)

    def test_demand_gap(self) -> None:
        tracker = JJMTracker()
        tracker.update(make_fhtc_status(total_households=500, fhtc_provided=350))
        gap = tracker.demand_gap("GP001")
        assert gap == 150

    def test_demand_gap_nonexistent(self) -> None:
        tracker = JJMTracker()
        assert tracker.demand_gap("NONEXISTENT") == 0

    def test_lpcd_check_meets_standard(self) -> None:
        tracker = JJMTracker()
        # 1000 people, 60000 LPD = 60 LPCD (above 55)
        result = tracker.lpcd_check("GP001", 1000, 60000.0)
        assert result["actual_lpcd"] == 60.0
        assert result["required_lpcd"] == 55.0
        assert result["gap_lpd"] == 0.0

    def test_lpcd_check_below_standard(self) -> None:
        tracker = JJMTracker()
        # 1000 people, 40000 LPD = 40 LPCD (below 55)
        result = tracker.lpcd_check("GP001", 1000, 40000.0)
        assert result["actual_lpcd"] == 40.0
        assert result["gap_lpd"] > 0

    def test_lpcd_check_zero_population(self) -> None:
        tracker = JJMTracker()
        result = tracker.lpcd_check("GP001", 0, 0.0)
        assert result["actual_lpcd"] == 0.0


# ---------------------------------------------------------------------------
# GroundwaterMonitor tests
# ---------------------------------------------------------------------------


class TestGroundwaterMonitor:
    def test_add_and_by_panchayat(self) -> None:
        monitor = GroundwaterMonitor()
        record = make_groundwater_record()
        monitor.add(record)
        results = monitor.by_panchayat("GP001")
        assert len(results) == 1

    def test_latest(self) -> None:
        monitor = GroundwaterMonitor()
        monitor.add(make_groundwater_record(year=2022, season=SeasonType.PRE_MONSOON, depth_meters=8.0))
        monitor.add(make_groundwater_record(year=2024, season=SeasonType.PRE_MONSOON, depth_meters=12.0))
        latest = monitor.latest("GP001")
        assert latest is not None
        assert latest.depth_meters == 12.0

    def test_latest_empty(self) -> None:
        monitor = GroundwaterMonitor()
        assert monitor.latest("GP001") is None

    def test_declining_trend_true(self) -> None:
        monitor = GroundwaterMonitor()
        monitor.add(make_groundwater_record(year=2022, season=SeasonType.PRE_MONSOON, depth_meters=8.0))
        monitor.add(make_groundwater_record(year=2023, season=SeasonType.PRE_MONSOON, depth_meters=10.0))
        monitor.add(make_groundwater_record(year=2024, season=SeasonType.PRE_MONSOON, depth_meters=12.0))
        assert monitor.declining_trend("GP001") is True

    def test_declining_trend_false(self) -> None:
        monitor = GroundwaterMonitor()
        monitor.add(make_groundwater_record(year=2022, season=SeasonType.PRE_MONSOON, depth_meters=12.0))
        monitor.add(make_groundwater_record(year=2023, season=SeasonType.PRE_MONSOON, depth_meters=10.0))
        monitor.add(make_groundwater_record(year=2024, season=SeasonType.PRE_MONSOON, depth_meters=8.0))
        assert monitor.declining_trend("GP001") is False

    def test_declining_trend_not_enough_data(self) -> None:
        monitor = GroundwaterMonitor()
        monitor.add(make_groundwater_record(year=2024, season=SeasonType.PRE_MONSOON, depth_meters=10.0))
        assert monitor.declining_trend("GP001") is False

    def test_categorize_level(self) -> None:
        monitor = GroundwaterMonitor()
        assert monitor.categorize_level(1.0) == "very_shallow"
        assert monitor.categorize_level(5.0) == "shallow"
        assert monitor.categorize_level(15.0) == "moderate"
        assert monitor.categorize_level(30.0) == "deep"
        assert monitor.categorize_level(50.0) == "very_deep"

    def test_recharge_potential_high(self) -> None:
        monitor = GroundwaterMonitor()
        monitor.add(GroundwaterLevel(panchayat_id="GP001", season=SeasonType.PRE_MONSOON, year=2024, depth_meters=15.0))
        monitor.add(GroundwaterLevel(panchayat_id="GP001", season=SeasonType.POST_MONSOON, year=2024, depth_meters=8.0))
        # Recovery = 15 - 8 = 7 meters > 5 → high
        assert monitor.recharge_potential("GP001") == "high"

    def test_recharge_potential_insufficient_data(self) -> None:
        monitor = GroundwaterMonitor()
        monitor.add(make_groundwater_record(season=SeasonType.PRE_MONSOON))
        assert monitor.recharge_potential("GP001") == "insufficient_data"

    def test_recharge_potential_negligible(self) -> None:
        monitor = GroundwaterMonitor()
        monitor.add(GroundwaterLevel(panchayat_id="GP001", season=SeasonType.PRE_MONSOON, year=2024, depth_meters=10.0))
        monitor.add(GroundwaterLevel(panchayat_id="GP001", season=SeasonType.POST_MONSOON, year=2024, depth_meters=10.5))
        # Recovery = 10 - 10.5 = -0.5 → negligible
        assert monitor.recharge_potential("GP001") == "negligible"


# ---------------------------------------------------------------------------
# RainfallAnalyzer tests
# ---------------------------------------------------------------------------


class TestRainfallAnalyzer:
    def test_annual_total(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=6, rainfall_mm=150.0))
        analyzer.add(make_rainfall_record(month=7, rainfall_mm=200.0))
        total = analyzer.annual_total("GP001", 2024)
        assert total == 350.0

    def test_annual_normal(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=6, normal_mm=130.0))
        analyzer.add(make_rainfall_record(month=7, normal_mm=180.0))
        normal = analyzer.annual_normal("GP001", 2024)
        assert normal == 310.0

    def test_annual_deviation_pct(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=7, rainfall_mm=200.0, normal_mm=160.0))
        dev = analyzer.annual_deviation_pct("GP001", 2024)
        assert dev == 25.0

    def test_drought_risk_severe(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=7, rainfall_mm=30.0, normal_mm=160.0))
        # Deviation ≈ -81% → severe
        risk = analyzer.drought_risk("GP001", 2024)
        assert risk == "severe_drought"

    def test_drought_risk_moderate(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=7, rainfall_mm=80.0, normal_mm=160.0))
        # Deviation = -50% → moderate
        risk = analyzer.drought_risk("GP001", 2024)
        assert risk == "moderate_drought"

    def test_drought_risk_mild(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=7, rainfall_mm=120.0, normal_mm=160.0))
        # Deviation = -25% → mild
        risk = analyzer.drought_risk("GP001", 2024)
        assert risk == "mild_drought"

    def test_drought_risk_normal(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=7, rainfall_mm=160.0, normal_mm=160.0))
        risk = analyzer.drought_risk("GP001", 2024)
        assert risk == "normal"

    def test_flood_risk_high(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=7, rainfall_mm=270.0, normal_mm=160.0))
        # Deviation > 68% → high flood risk
        risk = analyzer.flood_risk("GP001", 2024)
        assert risk == "high_flood_risk"

    def test_flood_risk_moderate(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=7, rainfall_mm=220.0, normal_mm=160.0))
        # Deviation = 37.5% → moderate
        risk = analyzer.flood_risk("GP001", 2024)
        assert risk == "moderate_flood_risk"

    def test_flood_risk_normal(self) -> None:
        analyzer = RainfallAnalyzer()
        analyzer.add(make_rainfall_record(month=7, rainfall_mm=165.0, normal_mm=160.0))
        risk = analyzer.flood_risk("GP001", 2024)
        assert risk == "normal"

    def test_monsoon_performance(self) -> None:
        analyzer = RainfallAnalyzer()
        for month in [6, 7, 8, 9]:
            analyzer.add(make_rainfall_record(month=month, rainfall_mm=200.0, normal_mm=180.0))
        perf = analyzer.monsoon_performance("GP001", 2024)
        assert perf["actual_mm"] == 800.0
        assert perf["normal_mm"] == 720.0
        assert perf["deviation_pct"] > 0


# ---------------------------------------------------------------------------
# WaterBudgetPlanner tests
# ---------------------------------------------------------------------------


class TestWaterBudgetPlanner:
    def test_estimate_demand_domestic_only(self) -> None:
        planner = WaterBudgetPlanner()
        budget = planner.estimate_demand(population=1000)
        assert budget.domestic_demand_lpd == 55000.0  # 1000 * 55

    def test_estimate_demand_with_livestock(self) -> None:
        planner = WaterBudgetPlanner()
        budget = planner.estimate_demand(population=1000, livestock=10)
        assert budget.agriculture_demand_lpd == 300.0  # 10 * 30

    def test_estimate_demand_total_includes_agriculture(self) -> None:
        planner = WaterBudgetPlanner()
        budget = planner.estimate_demand(population=1000, livestock=100, irrigated_hectares=0)
        # domestic = 55000, livestock = 3000, total = 58000
        assert budget.total_demand_lpd == 58000.0

    def test_sustainability_index_full(self) -> None:
        planner = WaterBudgetPlanner()
        budget = WaterBudget(
            panchayat_id="GP001",
            year=2024,
            total_demand_lpd=10000.0,
            total_supply_lpd=10000.0,
            domestic_demand_lpd=8000.0,
            agriculture_demand_lpd=2000.0,
            industrial_demand_lpd=0.0,
        )
        index = planner.sustainability_index(budget)
        assert index == 100.0

    def test_sustainability_index_deficit(self) -> None:
        planner = WaterBudgetPlanner()
        budget = WaterBudget(
            panchayat_id="GP001",
            year=2024,
            total_demand_lpd=10000.0,
            total_supply_lpd=5000.0,
            domestic_demand_lpd=8000.0,
            agriculture_demand_lpd=2000.0,
            industrial_demand_lpd=0.0,
        )
        index = planner.sustainability_index(budget)
        assert index == 50.0

    def test_sustainability_index_zero_demand(self) -> None:
        planner = WaterBudgetPlanner()
        budget = WaterBudget(
            panchayat_id="GP001",
            year=2024,
            total_demand_lpd=0.0,
            total_supply_lpd=0.0,
            domestic_demand_lpd=0.0,
            agriculture_demand_lpd=0.0,
            industrial_demand_lpd=0.0,
        )
        index = planner.sustainability_index(budget)
        assert index == 100.0

    def test_sustainability_index_capped_at_100(self) -> None:
        planner = WaterBudgetPlanner()
        budget = WaterBudget(
            panchayat_id="GP001",
            year=2024,
            total_demand_lpd=5000.0,
            total_supply_lpd=20000.0,
            domestic_demand_lpd=4000.0,
            agriculture_demand_lpd=1000.0,
            industrial_demand_lpd=0.0,
        )
        index = planner.sustainability_index(budget)
        assert index == 100.0


# ---------------------------------------------------------------------------
# AlertEngine tests
# ---------------------------------------------------------------------------


class TestAlertEngine:
    def test_check_quality_hazardous(self) -> None:
        engine = AlertEngine()
        report = make_clean_report()
        report.coliform_present = True
        alerts = engine.check_quality(report)
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.EMERGENCY

    def test_check_quality_contaminated(self) -> None:
        engine = AlertEngine()
        report = make_clean_report()
        report.tds_ppm = 800.0  # Contaminated
        alerts = engine.check_quality(report)
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING

    def test_check_quality_safe(self) -> None:
        engine = AlertEngine()
        report = make_clean_report()
        alerts = engine.check_quality(report)
        assert alerts == []

    def test_check_groundwater_very_deep(self) -> None:
        engine = AlertEngine()
        record = make_groundwater_record(depth_meters=45.0, previous_year_depth=40.0)
        alerts = engine.check_groundwater(record)
        assert any(a.level == AlertLevel.CRITICAL for a in alerts)

    def test_check_groundwater_deep(self) -> None:
        engine = AlertEngine()
        record = make_groundwater_record(depth_meters=25.0, previous_year_depth=23.0)
        alerts = engine.check_groundwater(record)
        assert any(a.level == AlertLevel.WARNING for a in alerts)

    def test_check_groundwater_declining_trend(self) -> None:
        engine = AlertEngine()
        record = make_groundwater_record(depth_meters=10.0, previous_year_depth=5.0)
        # Declining by 5m
        alerts = engine.check_groundwater(record)
        assert any(a.category == "groundwater_trend" for a in alerts)

    def test_check_supply_severe_scarcity(self) -> None:
        engine = AlertEngine()
        # 1000 people, only 20000 LPD = 20 LPCD (less than 27)
        alerts = engine.check_supply(1000, 20000.0)
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.EMERGENCY

    def test_check_supply_below_jjm(self) -> None:
        engine = AlertEngine()
        # 1000 people, 40000 LPD = 40 LPCD (between 27 and 55)
        alerts = engine.check_supply(1000, 40000.0)
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING

    def test_check_supply_adequate(self) -> None:
        engine = AlertEngine()
        # 1000 people, 60000 LPD = 60 LPCD (above 55)
        alerts = engine.check_supply(1000, 60000.0)
        assert alerts == []

    def test_check_supply_zero_population(self) -> None:
        engine = AlertEngine()
        alerts = engine.check_supply(0, 0.0)
        assert alerts == []

    def test_check_rainfall_drought(self) -> None:
        engine = AlertEngine()
        alerts = engine.check_rainfall("GP001", -45.0)
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.CRITICAL
        assert alerts[0].category == "drought"

    def test_check_rainfall_flood(self) -> None:
        engine = AlertEngine()
        alerts = engine.check_rainfall("GP001", 70.0)
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.CRITICAL
        assert alerts[0].category == "flood"

    def test_check_rainfall_normal(self) -> None:
        engine = AlertEngine()
        alerts = engine.check_rainfall("GP001", 10.0)
        assert alerts == []

    def test_alert_ids_are_unique(self) -> None:
        engine = AlertEngine()
        report1 = make_clean_report(report_id="R1")
        report1.coliform_present = True
        report2 = make_clean_report(report_id="R2")
        report2.coliform_present = True
        alerts1 = engine.check_quality(report1)
        alerts2 = engine.check_quality(report2)
        assert alerts1[0].alert_id != alerts2[0].alert_id
