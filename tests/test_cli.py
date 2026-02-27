"""Tests for aumai-jaldrishti CLI."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from aumai_jaldrishti.cli import main


def make_source_json() -> dict:
    return {
        "source_id": "SRC001",
        "panchayat_id": "GP001",
        "name": "Main Borewell",
        "source_type": "borewell",
        "latitude": 26.9,
        "longitude": 80.9,
        "capacity_liters_per_day": 10000.0,
        "current_yield_lpd": 7000.0,
        "is_functional": True,
    }


def make_quality_report_json() -> dict:
    return {
        "report_id": "RPT001",
        "source_id": "SRC001",
        "test_date": "2025-01-15",
        "ph": 7.0,
        "tds_ppm": 300.0,
        "turbidity_ntu": 0.5,
        "chloride_ppm": 100.0,
        "fluoride_ppm": 0.5,
        "arsenic_ppb": 2.0,
        "iron_ppm": 0.1,
        "nitrate_ppm": 20.0,
        "coliform_present": False,
    }


def make_fhtc_json() -> dict:
    return {
        "panchayat_id": "GP001",
        "panchayat_name": "Rampur",
        "total_households": 500,
        "fhtc_provided": 400,
        "fhtc_functional": 350,
    }


def make_groundwater_json() -> list[dict]:
    return [
        {"panchayat_id": "GP001", "season": "pre_monsoon", "year": 2022, "depth_meters": 8.0, "previous_year_depth": 7.0},
        {"panchayat_id": "GP001", "season": "pre_monsoon", "year": 2023, "depth_meters": 10.0, "previous_year_depth": 8.0},
        {"panchayat_id": "GP001", "season": "pre_monsoon", "year": 2024, "depth_meters": 12.0, "previous_year_depth": 10.0},
    ]


def make_rainfall_json() -> list[dict]:
    return [
        {"panchayat_id": "GP001", "month": m, "year": 2024, "rainfall_mm": 150.0, "normal_mm": 140.0}
        for m in range(1, 13)
    ]


class TestCLIVersion:
    def test_cli_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "JalDrishti" in result.output or "water" in result.output.lower()


class TestSourceCommand:
    def test_source_valid(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("source.json").write_text(json.dumps(make_source_json()))
            result = runner.invoke(main, ["source", "--input", "source.json"])
            assert result.exit_code == 0
            assert "Main Borewell" in result.output

    def test_source_shows_yield(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("source.json").write_text(json.dumps(make_source_json()))
            result = runner.invoke(main, ["source", "--input", "source.json"])
            assert "LPD" in result.output or "lpd" in result.output.lower()

    def test_source_missing_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["source", "--input", "nonexistent.json"])
        assert result.exit_code != 0


class TestQualityCommand:
    def test_quality_safe_report(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("report.json").write_text(json.dumps(make_quality_report_json()))
            result = runner.invoke(main, ["quality", "--input", "report.json"])
            assert result.exit_code == 0
            assert "SAFE" in result.output or "safe" in result.output.lower()

    def test_quality_shows_source_id(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("report.json").write_text(json.dumps(make_quality_report_json()))
            result = runner.invoke(main, ["quality", "--input", "report.json"])
            assert "SRC001" in result.output

    def test_quality_missing_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["quality", "--input", "nonexistent.json"])
        assert result.exit_code != 0


class TestFHTCCommand:
    def test_fhtc_valid(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("fhtc.json").write_text(json.dumps(make_fhtc_json()))
            result = runner.invoke(main, ["fhtc", "--input", "fhtc.json"])
            assert result.exit_code == 0
            assert "Rampur" in result.output

    def test_fhtc_shows_coverage(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("fhtc.json").write_text(json.dumps(make_fhtc_json()))
            result = runner.invoke(main, ["fhtc", "--input", "fhtc.json"])
            assert "80.0%" in result.output or "coverage" in result.output.lower()

    def test_fhtc_missing_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["fhtc", "--input", "nonexistent.json"])
        assert result.exit_code != 0


class TestGroundwaterCommand:
    def test_groundwater_valid(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("gw.json").write_text(json.dumps(make_groundwater_json()))
            result = runner.invoke(main, ["groundwater", "--input", "gw.json", "--panchayat", "GP001"])
            assert result.exit_code == 0
            assert "GP001" in result.output

    def test_groundwater_shows_depth(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("gw.json").write_text(json.dumps(make_groundwater_json()))
            result = runner.invoke(main, ["groundwater", "--input", "gw.json", "--panchayat", "GP001"])
            assert "m" in result.output or "depth" in result.output.lower()

    def test_groundwater_missing_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["groundwater", "--input", "nonexistent.json", "--panchayat", "GP001"])
        assert result.exit_code != 0


class TestRainfallCommand:
    def test_rainfall_valid(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("rain.json").write_text(json.dumps(make_rainfall_json()))
            result = runner.invoke(main, ["rainfall", "--input", "rain.json", "--panchayat", "GP001", "--year", "2024"])
            assert result.exit_code == 0

    def test_rainfall_shows_deviation(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("rain.json").write_text(json.dumps(make_rainfall_json()))
            result = runner.invoke(main, ["rainfall", "--input", "rain.json", "--panchayat", "GP001", "--year", "2024"])
            assert "Deviation" in result.output or "deviation" in result.output.lower()

    def test_rainfall_missing_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["rainfall", "--input", "nonexistent.json", "--panchayat", "GP001", "--year", "2024"])
        assert result.exit_code != 0


class TestBudgetCommand:
    def test_budget_basic(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["budget", "--population", "1000"])
        assert result.exit_code == 0
        assert "Water Budget" in result.output or "demand" in result.output.lower()

    def test_budget_shows_lpd(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["budget", "--population", "1000"])
        assert "LPD" in result.output

    def test_budget_with_supply(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["budget", "--population", "1000", "--supply-lpd", "60000"])
        assert result.exit_code == 0
        assert "Sustainability" in result.output or "LPCD" in result.output

    def test_budget_with_livestock(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["budget", "--population", "1000", "--livestock", "50"])
        assert result.exit_code == 0
