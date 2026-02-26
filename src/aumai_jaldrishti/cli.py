"""CLI entry point for aumai-jaldrishti."""

from __future__ import annotations

import json

import click

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
    WaterQualityReport,
    WaterSource,
)


@click.group()
@click.version_option()
def cli() -> None:
    """AumAI JalDrishti - Water resource management for Jal Jeevan Mission."""


@cli.command()
@click.option("--input", "input_file", required=True, type=click.Path(exists=True), help="Water source JSON file")
def source(input_file: str) -> None:
    """Register and analyze water sources."""
    with open(input_file) as f:
        data = json.load(f)

    manager = SourceManager()
    sources = data if isinstance(data, list) else [data]
    for item in sources:
        ws = WaterSource.model_validate(item)
        manager.register(ws)
        status = "Functional" if ws.is_functional else "Non-functional"
        click.echo(f"  [{status}] {ws.name} ({ws.source_type.value})")
        click.echo(f"    Yield: {ws.current_yield_lpd:,.0f} LPD ({ws.yield_pct:.0f}% capacity)")

    if sources:
        pid = WaterSource.model_validate(sources[0]).panchayat_id
        total = manager.total_supply_lpd(pid)
        click.echo(f"\nTotal supply for {pid}: {total:,.0f} liters/day")
        low = manager.low_yield_sources(pid)
        if low:
            click.echo(f"Low yield sources ({len(low)}):")
            for s in low:
                click.echo(f"  - {s.name}: {s.yield_pct:.0f}% capacity")


@cli.command()
@click.option("--input", "input_file", required=True, type=click.Path(exists=True), help="Water quality report JSON")
def quality(input_file: str) -> None:
    """Analyze water quality against BIS 10500:2012 standards."""
    with open(input_file) as f:
        data = json.load(f)

    analyzer = WaterQualityAnalyzer()
    reports = data if isinstance(data, list) else [data]

    for item in reports:
        report = WaterQualityReport.model_validate(item)
        grade = analyzer.grade_report(report)
        click.echo(f"\nSource {report.source_id} | Date: {report.test_date}")
        click.echo(f"  Grade: {grade.value.upper()}")
        click.echo(f"  pH: {report.ph} | TDS: {report.tds_ppm} ppm | Turbidity: {report.turbidity_ntu} NTU")

        issues = analyzer.identify_contaminants(report)
        if issues:
            click.echo("  Issues:")
            for issue in issues:
                click.echo(f"    - {issue}")

        treatments = analyzer.recommend_treatment(report)
        if treatments:
            click.echo("  Recommended treatment:")
            for t in treatments:
                click.echo(f"    - {t}")


@cli.command()
@click.option("--input", "input_file", required=True, type=click.Path(exists=True), help="FHTC status JSON file")
def fhtc(input_file: str) -> None:
    """Track Jal Jeevan Mission FHTC coverage."""
    with open(input_file) as f:
        data = json.load(f)

    tracker = JJMTracker()
    records = data if isinstance(data, list) else [data]
    for item in records:
        status = FHTCStatus.model_validate(item)
        tracker.update(status)

    click.echo("\nJal Jeevan Mission - FHTC Coverage Report")
    click.echo("=" * 55)

    for status in tracker.all_statuses():
        gap = tracker.demand_gap(status.panchayat_id)
        click.echo(f"\n{status.panchayat_name} ({status.panchayat_id})")
        click.echo(f"  Households: {status.total_households:,}")
        click.echo(f"  FHTC provided: {status.fhtc_provided:,} ({status.coverage_pct:.1f}%)")
        click.echo(f"  FHTC functional: {status.fhtc_functional:,} ({status.functional_pct:.1f}%)")
        if gap > 0:
            click.echo(f"  Gap: {gap:,} households without tap connection")

    summary = tracker.coverage_summary()
    click.echo(f"\nOverall: {summary['avg_coverage_pct']:.1f}% coverage, {summary['avg_functional_pct']:.1f}% functional")


@cli.command()
@click.option("--input", "input_file", required=True, type=click.Path(exists=True), help="Groundwater JSON file")
@click.option("--panchayat", required=True, help="Panchayat ID")
def groundwater(input_file: str, panchayat: str) -> None:
    """Monitor groundwater levels and trends."""
    with open(input_file) as f:
        data = json.load(f)

    monitor = GroundwaterMonitor()
    records = data if isinstance(data, list) else [data]
    for item in records:
        monitor.add(GroundwaterLevel.model_validate(item))

    click.echo(f"\nGroundwater Report: {panchayat}")
    click.echo("=" * 45)

    history = monitor.by_panchayat(panchayat)
    for record in history:
        category = monitor.categorize_level(record.depth_meters)
        trend = "v" if record.is_declining else "^"
        click.echo(f"  {record.year} {record.season.value:<15s} {record.depth_meters:>6.1f}m ({category}) {trend} {record.change_meters:+.1f}m")

    declining = monitor.declining_trend(panchayat)
    recharge = monitor.recharge_potential(panchayat)
    click.echo(f"\nDeclining trend (3yr): {'YES' if declining else 'No'}")
    click.echo(f"Recharge potential: {recharge}")

    latest = monitor.latest(panchayat)
    if latest:
        engine = AlertEngine()
        alerts = engine.check_groundwater(latest)
        for alert in alerts:
            click.echo(f"  [{alert.level.value.upper()}] {alert.message}")


@cli.command()
@click.option("--input", "input_file", required=True, type=click.Path(exists=True), help="Rainfall JSON file")
@click.option("--panchayat", required=True, help="Panchayat ID")
@click.option("--year", required=True, type=int, help="Year")
def rainfall(input_file: str, panchayat: str, year: int) -> None:
    """Analyze rainfall and drought/flood risk."""
    with open(input_file) as f:
        data = json.load(f)

    analyzer = RainfallAnalyzer()
    records = data if isinstance(data, list) else [data]
    for item in records:
        analyzer.add(RainfallRecord.model_validate(item))

    total = analyzer.annual_total(panchayat, year)
    normal = analyzer.annual_normal(panchayat, year)
    deviation = analyzer.annual_deviation_pct(panchayat, year)
    drought = analyzer.drought_risk(panchayat, year)
    flood = analyzer.flood_risk(panchayat, year)
    monsoon = analyzer.monsoon_performance(panchayat, year)

    click.echo(f"\nRainfall Analysis: {panchayat} | {year}")
    click.echo("=" * 45)
    click.echo(f"  Annual: {total:.0f} mm (normal: {normal:.0f} mm)")
    click.echo(f"  Deviation: {deviation:+.1f}%")
    click.echo(f"  Drought risk: {drought}")
    click.echo(f"  Flood risk: {flood}")
    click.echo(f"\n  Monsoon (Jun-Sep): {monsoon['actual_mm']:.0f} mm vs {monsoon['normal_mm']:.0f} mm ({monsoon['deviation_pct']:+.1f}%)")


@cli.command()
@click.option("--population", required=True, type=int, help="Village population")
@click.option("--livestock", default=0, type=int, help="Livestock count")
@click.option("--irrigated-ha", default=0.0, type=float, help="Irrigated hectares")
@click.option("--supply-lpd", default=0.0, type=float, help="Current supply (liters/day)")
def budget(population: int, livestock: int, irrigated_ha: float, supply_lpd: float) -> None:
    """Estimate water demand and supply gap."""
    planner = WaterBudgetPlanner()
    wb = planner.estimate_demand(population, livestock, irrigated_ha)
    wb.total_supply_lpd = supply_lpd

    click.echo("\nWater Budget Estimate")
    click.echo("=" * 40)
    click.echo(f"  Population: {population:,}")
    click.echo(f"  Domestic demand:     {wb.domestic_demand_lpd:>12,.0f} LPD")
    click.echo(f"  Agriculture demand:  {wb.agriculture_demand_lpd:>12,.0f} LPD")
    click.echo(f"  Total demand:        {wb.total_demand_lpd:>12,.0f} LPD")
    click.echo(f"  Current supply:      {supply_lpd:>12,.0f} LPD")
    click.echo(f"  Surplus/Deficit:     {wb.surplus_deficit_lpd:>+12,.0f} LPD")

    if supply_lpd > 0:
        index = planner.sustainability_index(wb)
        click.echo(f"\n  Sustainability index: {index:.0f}/100")
        lpcd = supply_lpd / population if population > 0 else 0
        click.echo(f"  LPCD: {lpcd:.0f} (JJM standard: 55)")

    click.echo("\nVerify water data with local authorities before making decisions.")


main = cli

if __name__ == "__main__":
    cli()
