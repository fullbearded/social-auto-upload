# 快手数据统计模块初始化
# Kuaishou Statistics Module

from .data_structures import (
    KuaishouVideoStats,
    KuaishouAccountSummary,
    KuaishouPeriodStats,
    KuaishouAnalyticsReport,
    KuaishouEndpoints
)

from .scraper import (
    KuaishouStatisticsScraper,
    get_kuaishou_statistics
)

from .analytics import (
    KuaishouDataProcessor
)

from .reporter import (
    KuaishouReportGenerator,
    ReportManager
)

from .storage import (
    KuaishouDataStorage
)

# CLI 工具（可选导入）
try:
    from .kuaishou_stats_cli import KuaishouStatsCLI
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False

__all__ = [
    # 数据结构类
    'KuaishouVideoStats',
    'KuaishouAccountSummary',
    'KuaishouPeriodStats',
    'KuaishouAnalyticsReport',
    'KuaishouEndpoints',
    
    # 数据采集
    'KuaishouStatisticsScraper',
    'get_kuaishou_statistics',
    
    # 数据分析
    'KuaishouDataProcessor',
    
    # 报告生成
    'KuaishouReportGenerator',
    'ReportManager',
    
    # 数据存储
    'KuaishouDataStorage',
    
    # CLI 工具
    'KuaishouStatsCLI' if CLI_AVAILABLE else None
]

# 简化接口
__all__ = [cls for cls in __all__ if cls is not None]

# 版本信息
__version__ = "1.0.0"
__author__ = "social-auto-upload"
__description__ = "快手数据统计分析套件"