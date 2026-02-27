"""Quickstart examples for aumai-jaldrishti.

This script demonstrates the five core workflows:
  1. Water source management and yield analysis
  2. Water quality grading and treatment recommendations
  3. JJM FHTC coverage tracking
  4. Groundwater level monitoring and trend detection
  5. Rainfall analysis and water budget planning

Run directly to verify your installation:

    python examples/quickstart.py

Water Disclaimer: This tool provides estimates only. Verify with local water
resource authorities and certified laboratory testing before making decisions.
"""

from __future__ import annotations

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
    FHTCStatus,
    GroundwaterLevel,
    RainfallRecord,
    SeasonType,
    WaterQualityGrade,
    WaterQualityReport,
    WaterSource,
    WaterSourceType,
)


def demo_source_management() -> None:
    """Demonstrate SourceManager for water source inventory and yield analysis.

    A panchayat may have multiple source types. SourceManager tracks
    functional vs non-functional status, yield percentages, and total
    supply available for LPCD calculations.
    """
    print("\n" + "=" * 60)
    print("DEMO 1: Water Source Management")
    print("=" * 60)

    manager = SourceManager()
    panchayat_id = "PAN-RAJPUR"

    # Register three sources for the panchayat
    sources = [
        WaterSource(
            source_id="BW-001",
            panchayat_id=panchayat_id,
            name="Main Borewell",
            source_type=WaterSourceType.BOREWELL,
            latitude=28.610,
            longitude=77.230,
            capacity_liters_per_day=50000,
            current_yield_lpd=38000,
            depth_meters=45,
            is_functional=True,
            last_tested_date="2025-11-01",
        ),
        WaterSource(
            source_id="HP-002",
            panchayat_id=panchayat_id,
            name="Ward 2 Handpump",
            source_type=WaterSourceType.HANDPUMP,
            latitude=28.612,
            longitude=77.225,
            capacity_liters_per_day=5000,
            current_yield_lpd=1800,  # 36% — below 40% threshold
            depth_meters=20,
            is_functional=True,
            last_tested_date="2025-10-15",
        ),
        WaterSource(
            source_id="OW-003",
            panchayat_id=panchayat_id,
            name="Old Open Well (Ward 3)",
            source_type=WaterSourceType.OPEN_WELL,
            latitude=28.608,
            longitude=77.228,
            capacity_liters_per_day=3000,
            current_yield_lpd=0,
            depth_meters=8,
            is_functional=False,  # currently non-functional
        ),
    ]
    for source in sources:
        manager.register(source)

    # Summarise
    print(f"\nPanchayat: {panchayat_id}")
    print(f"Total sources registered: {len(manager.by_panchayat(panchayat_id))}")
    print(f"Functional sources: {len(manager.functional_sources(panchayat_id))}")
    print(f"Non-functional sources: {len(manager.non_functional_sources(panchayat_id))}")
    print(f"Total supply (functional): {manager.total_supply_lpd(panchayat_id):,.0f} LPD")

    # Yield percentages
    print("\nSource yield analysis:")
    for source in manager.by_panchayat(panchayat_id):
        status = "functional" if source.is_functional else "non-functional"
        print(f"  {source.name}: {source.yield_pct:.0f}% capacity ({status})")

    # Low-yield alert
    low_yield = manager.low_yield_sources(panchayat_id, threshold_pct=40.0)
    if low_yield:
        print(f"\nLow-yield sources (< 40% capacity):")
        for s in low_yield:
            print(f"  - {s.name}: {s.yield_pct:.0f}%")


def demo_water_quality() -> None:
    """Demonstrate WaterQualityAnalyzer and AlertEngine for two samples.

    Sample A is safe water. Sample B has coliform bacteria and excess fluoride —
    graded HAZARDOUS — triggering an EMERGENCY alert.
    """
    print("\n" + "=" * 60)
    print("DEMO 2: Water Quality Analysis")
    print("=" * 60)

    analyzer = WaterQualityAnalyzer()
    engine = AlertEngine()

    # Sample A — safe water, all parameters within BIS acceptable limits
    sample_a = WaterQualityReport(
        report_id="RPT-A",
        source_id="BW-001",
        test_date="2025-11-01",
        ph=7.2,
        tds_ppm=350,
        turbidity_ntu=0.5,
        chloride_ppm=120,
        fluoride_ppm=0.5,
        arsenic_ppb=1,
        iron_ppm=0.1,
        nitrate_ppm=20,
        coliform_present=False,
        grade=WaterQualityGrade.SAFE,
    )

    # Sample B — hazardous: coliform present, fluoride exceeds permissible limit
    sample_b = WaterQualityReport(
        report_id="RPT-B",
        source_id="HP-002",
        test_date="2025-11-01",
        ph=7.0,
        tds_ppm=300,
        turbidity_ntu=1.0,
        chloride_ppm=100,
        fluoride_ppm=2.1,    # BIS permissible = 1.5 ppm
        arsenic_ppb=0,
        iron_ppm=0.2,
        nitrate_ppm=20,
        coliform_present=True,  # hazardous regardless of other params
        grade=WaterQualityGrade.HAZARDOUS,
    )

    for report in [sample_a, sample_b]:
        grade = analyzer.grade_report(report)
        contaminants = analyzer.identify_contaminants(report)
        treatments = analyzer.recommend_treatment(report)
        alerts = engine.check_quality(report)

        print(f"\nSource {report.source_id}:")
        print(f"  Quality grade: {grade.value.upper()}")
        print(f"  pH: {report.ph} | TDS: {report.tds_ppm} ppm | Turbidity: {report.turbidity_ntu} NTU")

        if contaminants:
            print("  Parameters exceeding BIS limits:")
            for issue in contaminants:
                print(f"    - {issue}")
        else:
            print("  All parameters within BIS acceptable limits")

        if treatments:
            print("  Recommended treatment:")
            for treatment in treatments:
                print(f"    - {treatment}")

        if alerts:
            for alert in alerts:
                print(f"  [{alert.level.value.upper()}] {alert.message}")
        else:
            print("  No alerts generated")


def demo_jjm_tracker() -> None:
    """Demonstrate JJMTracker for FHTC coverage and LPCD checks.

    The JJM standard is 55 LPCD per person from a functional tap connection.
    JJMTracker tracks coverage gaps and flags panchayats below target.
    """
    print("\n" + "=" * 60)
    print("DEMO 3: JJM FHTC Coverage Tracking")
    print("=" * 60)

    tracker = JJMTracker()

    panchayat_data = [
        FHTCStatus(
            panchayat_id="PAN-A",
            panchayat_name="Rajpur GP",
            total_households=500,
            fhtc_provided=350,
            fhtc_functional=310,
            target_date="2024-03-31",
            report_date="2025-11-01",
        ),
        FHTCStatus(
            panchayat_id="PAN-B",
            panchayat_name="Keshavpur GP",
            total_households=300,
            fhtc_provided=300,
            fhtc_functional=285,
            target_date="2024-03-31",
            report_date="2025-11-01",
        ),
        FHTCStatus(
            panchayat_id="PAN-C",
            panchayat_name="Devapur GP",
            total_households=800,
            fhtc_provided=400,  # only 50% coverage
            fhtc_functional=380,
            target_date="2024-03-31",
            report_date="2025-11-01",
        ),
    ]

    for status in panchayat_data:
        tracker.update(status)

    # Per-panchayat report
    print("\nPer-panchayat FHTC status:")
    for status in tracker.all_statuses():
        gap = tracker.demand_gap(status.panchayat_id)
        print(f"\n  {status.panchayat_name}:")
        print(f"    Coverage:   {status.coverage_pct:.1f}% ({status.fhtc_provided}/{status.total_households})")
        print(f"    Functional: {status.functional_pct:.1f}%")
        if gap > 0:
            print(f"    Gap: {gap} households without tap connection")

    # Aggregate summary
    summary = tracker.coverage_summary()
    print(f"\nAggregate summary:")
    print(f"  Average coverage: {summary['avg_coverage_pct']:.1f}%")
    print(f"  Average functional: {summary['avg_functional_pct']:.1f}%")

    # Panchayats below 80% target
    below = tracker.below_target(target_pct=80.0)
    print(f"\nPanchayats below 80% coverage: {len(below)}")
    for s in below:
        print(f"  - {s.panchayat_name}: {s.coverage_pct:.1f}%")

    # LPCD check for PAN-A (population 2000, supply from demo 1 = 39,800 LPD)
    lpcd = tracker.lpcd_check("PAN-A", population=2000, total_supply_lpd=39800)
    print(f"\nLPCD check for PAN-A (pop. 2000):")
    print(f"  Actual LPCD:   {lpcd['actual_lpcd']:.1f} LPD/person")
    print(f"  JJM standard:  {lpcd['required_lpcd']:.0f} LPD/person")
    print(f"  Shortfall:     {lpcd['gap_lpd']:,.0f} LPD")


def demo_groundwater_monitor() -> None:
    """Demonstrate GroundwaterMonitor for seasonal depth tracking and trends.

    Pre-monsoon groundwater depth increases year-over-year indicate a declining
    water table — a critical signal for conservation intervention planning.
    """
    print("\n" + "=" * 60)
    print("DEMO 4: Groundwater Monitoring")
    print("=" * 60)

    monitor = GroundwaterMonitor()
    engine = AlertEngine()
    panchayat_id = "PAN-RAJPUR"

    # Three years of pre-monsoon and post-monsoon measurements
    measurements = [
        (2022, SeasonType.PRE_MONSOON,  10.0,  0.0),
        (2022, SeasonType.POST_MONSOON,  6.0,  0.0),
        (2023, SeasonType.PRE_MONSOON,  12.5, 10.0),
        (2023, SeasonType.POST_MONSOON,  7.5,  0.0),
        (2024, SeasonType.PRE_MONSOON,  15.2, 12.5),
        (2024, SeasonType.POST_MONSOON,  9.0,  0.0),
    ]

    for year, season, depth, prev_depth in measurements:
        monitor.add(GroundwaterLevel(
            panchayat_id=panchayat_id,
            season=season,
            year=year,
            depth_meters=depth,
            previous_year_depth=prev_depth,
        ))

    # Historical record
    print(f"\nGroundwater history for {panchayat_id}:")
    for record in monitor.by_panchayat(panchayat_id):
        trend_symbol = "v" if record.is_declining else "^"
        category = monitor.categorize_level(record.depth_meters)
        print(f"  {record.year} {record.season.value:<15s} "
              f"{record.depth_meters:5.1f}m ({category}) "
              f"{trend_symbol} {record.change_meters:+.1f}m")

    declining = monitor.declining_trend(panchayat_id, years=3)
    recharge = monitor.recharge_potential(panchayat_id)
    print(f"\nDeclining 3-year trend: {'YES — intervention recommended' if declining else 'No'}")
    print(f"Recharge potential: {recharge}")

    # Alerts from latest reading
    latest = monitor.latest(panchayat_id)
    if latest:
        alerts = engine.check_groundwater(latest)
        print(f"\nAlerts from latest reading ({latest.depth_meters}m, {latest.season.value}):")
        if alerts:
            for alert in alerts:
                print(f"  [{alert.level.value.upper()}] {alert.message}")
        else:
            print("  No alerts")


def demo_rainfall_and_budget() -> None:
    """Demonstrate RainfallAnalyzer drought risk and WaterBudgetPlanner.

    IMD drought classification is applied to annual rainfall deviation.
    WaterBudgetPlanner shows whether supply meets demand across all sectors.
    """
    print("\n" + "=" * 60)
    print("DEMO 5: Rainfall Analysis and Water Budget Planning")
    print("=" * 60)

    # Rainfall analysis
    rainfall_analyzer = RainfallAnalyzer()
    panchayat_id = "PAN-RAJPUR"
    year = 2024

    # Add monthly data — 2024 was a below-normal year
    monthly_data = [
        (1, 12, 15), (2, 8, 12), (3, 6, 9), (4, 5, 8),
        (5, 10, 18), (6, 65, 110), (7, 120, 200), (8, 100, 190),
        (9, 45, 120), (10, 20, 30), (11, 5, 10), (12, 2, 5),
    ]
    for month, actual_mm, normal_mm in monthly_data:
        rainfall_analyzer.add(RainfallRecord(
            panchayat_id=panchayat_id,
            month=month,
            year=year,
            rainfall_mm=actual_mm,
            normal_mm=normal_mm,
        ))

    annual_total = rainfall_analyzer.annual_total(panchayat_id, year)
    annual_normal = rainfall_analyzer.annual_normal(panchayat_id, year)
    deviation = rainfall_analyzer.annual_deviation_pct(panchayat_id, year)
    drought_risk = rainfall_analyzer.drought_risk(panchayat_id, year)
    flood_risk = rainfall_analyzer.flood_risk(panchayat_id, year)
    monsoon = rainfall_analyzer.monsoon_performance(panchayat_id, year)

    print(f"\nRainfall Analysis: {panchayat_id} | {year}")
    print(f"  Annual total:  {annual_total:.0f} mm  (normal: {annual_normal:.0f} mm)")
    print(f"  Deviation:     {deviation:+.1f}%")
    print(f"  Drought risk:  {drought_risk}")
    print(f"  Flood risk:    {flood_risk}")
    print(f"\n  Monsoon (Jun-Sep):")
    print(f"    Actual: {monsoon['actual_mm']:.0f} mm | Normal: {monsoon['normal_mm']:.0f} mm | "
          f"Deviation: {monsoon['deviation_pct']:+.1f}%")

    # Rainfall alert
    engine = AlertEngine()
    rain_alerts = engine.check_rainfall(panchayat_id, deviation)
    if rain_alerts:
        for alert in rain_alerts:
            print(f"\n  [{alert.level.value.upper()}] {alert.message}")
    else:
        print("\n  No drought/flood alerts generated")

    # Water budget
    print("\n" + "-" * 40)
    print("Water Budget Planning")
    print("-" * 40)

    planner = WaterBudgetPlanner()

    # Scenario: 2500 people, 300 livestock, 80 ha irrigation
    budget = planner.estimate_demand(population=2500, livestock=300, irrigated_hectares=80)
    current_supply = 120000  # LPD currently available

    budget.total_supply_lpd = current_supply
    sustainability = planner.sustainability_index(budget)
    lpcd = current_supply / 2500

    print(f"\n  Population: 2,500")
    print(f"  Domestic demand:    {budget.domestic_demand_lpd:>12,.0f} LPD")
    print(f"  Agriculture demand: {budget.agriculture_demand_lpd:>12,.0f} LPD")
    print(f"  Total demand:       {budget.total_demand_lpd:>12,.0f} LPD")
    print(f"  Current supply:     {current_supply:>12,.0f} LPD")
    print(f"  Surplus/Deficit:    {budget.surplus_deficit_lpd:>+12,.0f} LPD")
    print(f"\n  Sustainability index: {sustainability:.0f}/100")
    print(f"  Actual LPCD: {lpcd:.0f} (JJM standard: 55)")

    # Supply alert
    supply_alerts = engine.check_supply(population=2500, total_supply_lpd=current_supply)
    if supply_alerts:
        for alert in supply_alerts:
            print(f"\n  [{alert.level.value.upper()}] {alert.message}")
    else:
        print("\n  Supply meets JJM standard — no alerts")

    print("\nVerify water quality data with local authorities before consumption decisions.")


def main() -> None:
    """Run all quickstart demonstrations."""
    print("aumai-jaldrishti Quickstart")
    print("\nWater Disclaimer: This tool provides estimates only.")
    print("Verify with local water resource authorities and certified lab testing.")

    demo_source_management()
    demo_water_quality()
    demo_jjm_tracker()
    demo_groundwater_monitor()
    demo_rainfall_and_budget()

    print("\n" + "=" * 60)
    print("All demos complete.")
    print("See docs/api-reference.md for full API documentation.")
    print("=" * 60)


if __name__ == "__main__":
    main()
