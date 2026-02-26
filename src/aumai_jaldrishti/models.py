"""Pydantic models for aumai-jaldrishti."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


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


class WaterQualityGrade(str, Enum):
    SAFE = "safe"
    ACCEPTABLE = "acceptable"
    CONTAMINATED = "contaminated"
    HAZARDOUS = "hazardous"


class SeasonType(str, Enum):
    PRE_MONSOON = "pre_monsoon"
    MONSOON = "monsoon"
    POST_MONSOON = "post_monsoon"
    WINTER = "winter"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class WaterSource(BaseModel):
    source_id: str
    panchayat_id: str
    name: str
    source_type: WaterSourceType
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    capacity_liters_per_day: float = Field(ge=0)
    current_yield_lpd: float = Field(ge=0)
    depth_meters: float = Field(ge=0, default=0)
    is_functional: bool = True
    last_tested_date: str = ""

    @property
    def yield_pct(self) -> float:
        if self.capacity_liters_per_day == 0:
            return 0.0
        return round((self.current_yield_lpd / self.capacity_liters_per_day) * 100, 1)


class WaterQualityReport(BaseModel):
    report_id: str
    source_id: str
    test_date: str
    ph: float = Field(ge=0, le=14)
    tds_ppm: float = Field(ge=0)
    turbidity_ntu: float = Field(ge=0)
    chloride_ppm: float = Field(ge=0, default=0)
    fluoride_ppm: float = Field(ge=0, default=0)
    arsenic_ppb: float = Field(ge=0, default=0)
    iron_ppm: float = Field(ge=0, default=0)
    nitrate_ppm: float = Field(ge=0, default=0)
    coliform_present: bool = False
    grade: WaterQualityGrade = WaterQualityGrade.SAFE


class FHTCStatus(BaseModel):
    """Functional Household Tap Connection status per Jal Jeevan Mission."""
    panchayat_id: str
    panchayat_name: str
    total_households: int = Field(ge=0)
    fhtc_provided: int = Field(ge=0)
    fhtc_functional: int = Field(ge=0)
    target_date: str = ""
    report_date: str = ""

    @property
    def coverage_pct(self) -> float:
        if self.total_households == 0:
            return 0.0
        return round((self.fhtc_provided / self.total_households) * 100, 1)

    @property
    def functional_pct(self) -> float:
        if self.fhtc_provided == 0:
            return 0.0
        return round((self.fhtc_functional / self.fhtc_provided) * 100, 1)


class GroundwaterLevel(BaseModel):
    panchayat_id: str
    season: SeasonType
    year: int
    depth_meters: float = Field(ge=0)
    previous_year_depth: float = Field(ge=0, default=0)

    @property
    def change_meters(self) -> float:
        return round(self.depth_meters - self.previous_year_depth, 2)

    @property
    def is_declining(self) -> bool:
        return self.depth_meters > self.previous_year_depth


class WaterAlert(BaseModel):
    alert_id: str
    panchayat_id: str
    level: AlertLevel
    category: str
    message: str
    source_id: str = ""
    date: str = ""
    is_active: bool = True


class WaterBudget(BaseModel):
    panchayat_id: str
    year: int
    total_demand_lpd: float = Field(ge=0)
    total_supply_lpd: float = Field(ge=0)
    domestic_demand_lpd: float = Field(ge=0)
    agriculture_demand_lpd: float = Field(ge=0)
    industrial_demand_lpd: float = Field(ge=0)

    @property
    def surplus_deficit_lpd(self) -> float:
        return round(self.total_supply_lpd - self.total_demand_lpd, 0)

    @property
    def is_deficit(self) -> bool:
        return self.total_supply_lpd < self.total_demand_lpd


class RainfallRecord(BaseModel):
    panchayat_id: str
    month: int = Field(ge=1, le=12)
    year: int
    rainfall_mm: float = Field(ge=0)
    normal_mm: float = Field(ge=0)

    @property
    def deviation_pct(self) -> float:
        if self.normal_mm == 0:
            return 0.0
        return round(((self.rainfall_mm - self.normal_mm) / self.normal_mm) * 100, 1)


__all__ = [
    "WaterSourceType", "WaterQualityGrade", "SeasonType", "AlertLevel",
    "WaterSource", "WaterQualityReport", "FHTCStatus", "GroundwaterLevel",
    "WaterAlert", "WaterBudget", "RainfallRecord",
]
