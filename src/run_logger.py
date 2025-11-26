"""
Reconciliation Run Logger
Logs comprehensive details for each reconciliation run including:
- Timestamp
- Volume comparison
- Record-level discrepancies
- Exception list
- Success/failure confirmation
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from .logger_config import get_logger
    from .discrepancy_tracker import DiscrepancyTracker
except ImportError:
    from logger_config import get_logger
    from discrepancy_tracker import DiscrepancyTracker

logger = get_logger("reconciliation.run")


class RunStatus(Enum):
    """Status of a reconciliation run."""
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_WITH_DISCREPANCIES = "COMPLETED_WITH_DISCREPANCIES"
    FAILED = "FAILED"


@dataclass
class VolumeComparison:
    """Comparison of record volumes between systems."""
    source_system: str
    target_system: str
    source_total: int
    target_total: int
    matched_count: int
    unmatched_count: int

    def to_dict(self) -> Dict:
        return {
            'source_system': self.source_system,
            'target_system': self.target_system,
            'source_total': self.source_total,
            'target_total': self.target_total,
            'matched_count': self.matched_count,
            'unmatched_count': self.unmatched_count,
            'volume_difference': abs(self.source_total - self.target_total),
            'match_rate': round((self.matched_count / max(self.source_total, 1)) * 100, 2)
        }


@dataclass
class ReconciliationRunLog:
    """Complete log entry for a single reconciliation run."""
    run_id: str
    status: RunStatus
    start_timestamp: datetime
    end_timestamp: Optional[datetime]
    volume_comparison: Optional[VolumeComparison]
    discrepancy_summary: Dict[str, Any]
    exception_list: List[Dict]
    error_message: Optional[str]

    def to_dict(self) -> Dict:
        return {
            'run_id': self.run_id,
            'status': self.status.value,
            'start_timestamp': self.start_timestamp.isoformat(),
            'end_timestamp': self.end_timestamp.isoformat() if self.end_timestamp else None,
            'duration_seconds': (self.end_timestamp - self.start_timestamp).total_seconds() if self.end_timestamp else None,
            'volume_comparison': self.volume_comparison.to_dict() if self.volume_comparison else None,
            'discrepancy_summary': self.discrepancy_summary,
            'exception_list': self.exception_list,
            'success': self.status in [RunStatus.COMPLETED_SUCCESS, RunStatus.COMPLETED_WITH_DISCREPANCIES],
            'error_message': self.error_message
        }


class ReconciliationRunLogger:
    """
    Manages logging for reconciliation runs.
    Each run captures:
    - Timestamp
    - Volume comparison
    - Record-level discrepancies
    - Exception list
    - Confirmation of success or failure
    """

    def __init__(self, run_id: str = None):
        self.run_id = run_id or f"RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4]}"
        self.start_timestamp = datetime.now()
        self.end_timestamp: Optional[datetime] = None
        self.status = RunStatus.STARTED
        self.volume_comparison: Optional[VolumeComparison] = None
        self.discrepancy_tracker: Optional[DiscrepancyTracker] = None
        self.error_message: Optional[str] = None

        self._log_run_start()

    def _log_run_start(self):
        """Log the start of a reconciliation run."""
        logger.info("=" * 80)
        logger.info(f"RECONCILIATION RUN STARTED")
        logger.info(f"Run ID: {self.run_id}")
        logger.info(f"Timestamp: {self.start_timestamp.isoformat()}")
        logger.info("=" * 80)

    def set_discrepancy_tracker(self, tracker: DiscrepancyTracker):
        """Associate a discrepancy tracker with this run."""
        self.discrepancy_tracker = tracker
        self.status = RunStatus.IN_PROGRESS
        logger.debug(f"Discrepancy tracker associated: {tracker.run_id}")

    def log_volume_comparison(
        self,
        source_system: str,
        target_system: str,
        source_total: int,
        target_total: int,
        matched_count: int
    ):
        """
        Log volume comparison between source and target systems.
        """
        unmatched = source_total - matched_count

        self.volume_comparison = VolumeComparison(
            source_system=source_system,
            target_system=target_system,
            source_total=source_total,
            target_total=target_total,
            matched_count=matched_count,
            unmatched_count=unmatched
        )

        logger.info("-" * 60)
        logger.info("VOLUME COMPARISON")
        logger.info("-" * 60)
        logger.info(f"Source System ({source_system}): {source_total} records")
        logger.info(f"Target System ({target_system}): {target_total} records")
        logger.info(f"Volume Difference: {abs(source_total - target_total)}")
        logger.info(f"Matched Records: {matched_count}")
        logger.info(f"Unmatched Records: {unmatched}")
        logger.info(f"Match Rate: {round((matched_count / max(source_total, 1)) * 100, 2)}%")
        logger.info("-" * 60)

    def log_discrepancy_summary(self):
        """Log summary of all discrepancies found."""
        if not self.discrepancy_tracker:
            logger.warning("No discrepancy tracker set - cannot log discrepancy summary")
            return

        summary = self.discrepancy_tracker.get_summary()

        logger.info("-" * 60)
        logger.info("RECORD-LEVEL DISCREPANCIES")
        logger.info("-" * 60)
        logger.info(f"Total Discrepancies: {summary['total_discrepancies']}")
        logger.info("")
        logger.info("By Type:")
        logger.info(f"  - Missing Records: {summary['by_type']['missing_records']}")
        logger.info(f"  - Unmatched Transactions: {summary['by_type']['unmatched_transactions']}")
        logger.info(f"  - Duplicate Records: {summary['by_type']['duplicate_records']}")
        logger.info(f"  - Count Discrepancies: {summary['by_type']['count_discrepancies']}")
        logger.info("")
        logger.info("By Severity:")
        logger.info(f"  - CRITICAL: {summary['by_severity']['critical']}")
        logger.info(f"  - HIGH: {summary['by_severity']['high']}")
        logger.info(f"  - MEDIUM: {summary['by_severity']['medium']}")
        logger.info(f"  - LOW: {summary['by_severity']['low']}")
        logger.info("-" * 60)

    def log_exception_list(self):
        """Log the exception list (all discrepancies sorted by severity)."""
        if not self.discrepancy_tracker:
            logger.warning("No discrepancy tracker set - cannot log exception list")
            return

        exception_list = self.discrepancy_tracker.get_exception_list()

        logger.info("-" * 60)
        logger.info("EXCEPTION LIST")
        logger.info("-" * 60)

        if not exception_list:
            logger.info("No exceptions found - all records reconciled successfully")
        else:
            for i, exception in enumerate(exception_list, 1):
                logger.info(
                    f"{i}. [{exception['severity']}] {exception['discrepancy_type'].upper()} | "
                    f"ID: {exception['discrepancy_id']} | "
                    f"TXN: {exception.get('transaction_id', 'N/A')} | "
                    f"{exception['description']}"
                )

        logger.info("-" * 60)

    def complete_run(self, success: bool = True, error_message: str = None):
        """
        Complete the reconciliation run and log final status.
        """
        self.end_timestamp = datetime.now()
        self.error_message = error_message

        if not success:
            self.status = RunStatus.FAILED
        elif self.discrepancy_tracker and self.discrepancy_tracker.discrepancies:
            self.status = RunStatus.COMPLETED_WITH_DISCREPANCIES
        else:
            self.status = RunStatus.COMPLETED_SUCCESS

        duration = (self.end_timestamp - self.start_timestamp).total_seconds()

        logger.info("=" * 80)
        logger.info("RECONCILIATION RUN COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Run ID: {self.run_id}")
        logger.info(f"Status: {self.status.value}")
        logger.info(f"Start Time: {self.start_timestamp.isoformat()}")
        logger.info(f"End Time: {self.end_timestamp.isoformat()}")
        logger.info(f"Duration: {duration:.2f} seconds")

        if self.error_message:
            logger.error(f"Error: {self.error_message}")

        if self.status == RunStatus.COMPLETED_SUCCESS:
            logger.info("RESULT: SUCCESS - All records reconciled without discrepancies")
        elif self.status == RunStatus.COMPLETED_WITH_DISCREPANCIES:
            disc_count = len(self.discrepancy_tracker.discrepancies) if self.discrepancy_tracker else 0
            logger.warning(f"RESULT: COMPLETED WITH {disc_count} DISCREPANCIES - Review required")
        else:
            logger.error("RESULT: FAILED - Reconciliation did not complete successfully")

        logger.info("=" * 80)

    def get_run_log(self) -> ReconciliationRunLog:
        """Get the complete run log as a data object."""
        discrepancy_summary = {}
        exception_list = []

        if self.discrepancy_tracker:
            discrepancy_summary = self.discrepancy_tracker.get_summary()
            exception_list = self.discrepancy_tracker.get_exception_list()

        return ReconciliationRunLog(
            run_id=self.run_id,
            status=self.status,
            start_timestamp=self.start_timestamp,
            end_timestamp=self.end_timestamp,
            volume_comparison=self.volume_comparison,
            discrepancy_summary=discrepancy_summary,
            exception_list=exception_list,
            error_message=self.error_message
        )

    def save_run_log(self, filepath: str = None) -> str:
        """Save the complete run log to a JSON file."""
        if filepath is None:
            project_root = Path(__file__).parent.parent
            logs_dir = project_root / "data" / "run_logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            filepath = logs_dir / f"run_log_{self.run_id}.json"

        run_log = self.get_run_log()

        with open(filepath, 'w') as f:
            json.dump(run_log.to_dict(), f, indent=2)

        logger.info(f"Run log saved to: {filepath}")
        return str(filepath)
