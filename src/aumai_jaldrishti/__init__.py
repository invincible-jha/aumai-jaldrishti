"""AumAI JalDrishti - Water resource management for Jal Jeevan Mission."""

__version__ = "0.1.0"

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

__all__ = [
    "AlertEngine",
    "AlertLevel",
    "FHTCStatus",
    "GroundwaterLevel",
    "GroundwaterMonitor",
    "JJMTracker",
    "RainfallAnalyzer",
    "RainfallRecord",
    "SeasonType",
    "SourceManager",
    "WaterAlert",
    "WaterBudget",
    "WaterBudgetPlanner",
    "WaterQualityAnalyzer",
    "WaterQualityGrade",
    "WaterQualityReport",
    "WaterSource",
    "WaterSourceType",
]
