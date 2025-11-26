"""
Discrepancy Tracker Module
Tracks and categorizes reconciliation discrepancies with detailed logging.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path

try:
    from .logger_config import get_logger
except ImportError:
    from logger_config import get_logger

logger = get_logger("reconciliation.discrepancy")


class DiscrepancyType(Enum):
    """Types of discrepancies that can be identified during reconciliation."""
    MISSING_RECORD = "missing_record"
    UNMATCHED_TRANSACTION = "unmatched_transaction"
    DUPLICATE_RECORD = "duplicate_record"
    COUNT_DISCREPANCY = "count_discrepancy"
    FIELD_MISMATCH = "field_mismatch"


class Severity(Enum):
    """Severity levels for discrepancies."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Discrepancy:
    """Represents a single discrepancy found during reconciliation."""
    discrepancy_id: str
    discrepancy_type: DiscrepancyType
    severity: Severity
    transaction_id: Optional[str]
    description: str
    source_system: str
    target_system: str
    details: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'discrepancy_id': self.discrepancy_id,
            'discrepancy_type': self.discrepancy_type.value,
            'severity': self.severity.value,
            'transaction_id': self.transaction_id,
            'description': self.description,
            'source_system': self.source_system,
            'target_system': self.target_system,
            'details': self.details,
            'timestamp': self.timestamp
        }


class DiscrepancyTracker:
    """
    Tracks all discrepancies found during a reconciliation run.
    Provides categorization, logging, and reporting capabilities.
    """

    def __init__(self, run_id: str = None):
        self.run_id = run_id or str(uuid.uuid4())[:8]
        self.discrepancies: List[Discrepancy] = []
        self.start_time = datetime.now()

        # Counters by type
        self.missing_records: List[Discrepancy] = []
        self.unmatched_transactions: List[Discrepancy] = []
        self.duplicate_records: List[Discrepancy] = []
        self.count_discrepancies: List[Discrepancy] = []
        self.field_mismatches: List[Discrepancy] = []

        logger.info(f"Discrepancy tracker initialized for run: {self.run_id}")

    def _generate_id(self) -> str:
        """Generate a unique discrepancy ID."""
        return f"DISC-{self.run_id}-{len(self.discrepancies) + 1:04d}"

    def add_missing_record(
        self,
        transaction_id: str,
        source_system: str,
        target_system: str,
        transaction_details: Dict[str, Any],
        severity: Severity = Severity.HIGH
    ) -> Discrepancy:
        """
        Record a missing record discrepancy.
        A transaction exists in source but is missing in target.
        """
        discrepancy = Discrepancy(
            discrepancy_id=self._generate_id(),
            discrepancy_type=DiscrepancyType.MISSING_RECORD,
            severity=severity,
            transaction_id=transaction_id,
            description=f"Transaction {transaction_id} missing in {target_system}",
            source_system=source_system,
            target_system=target_system,
            details={
                'transaction': transaction_details,
                'expected_in': target_system,
                'present_in': source_system
            }
        )

        self.discrepancies.append(discrepancy)
        self.missing_records.append(discrepancy)

        logger.warning(
            f"MISSING RECORD: {transaction_id} | "
            f"Present in {source_system}, missing in {target_system} | "
            f"Amount: {transaction_details.get('amount', 'N/A')} {transaction_details.get('currency', '')}"
        )

        return discrepancy

    def add_unmatched_transaction(
        self,
        transaction_id: str,
        source_system: str,
        target_system: str,
        source_details: Dict[str, Any],
        target_details: Dict[str, Any],
        field_differences: List[Dict[str, Any]],
        severity: Severity = Severity.MEDIUM
    ) -> Discrepancy:
        """
        Record an unmatched transaction discrepancy.
        Transaction exists in both systems but field values don't match.
        """
        # Upgrade severity if critical fields differ
        critical_fields = {'amount', 'currency'}
        if any(diff['field'] in critical_fields for diff in field_differences):
            severity = Severity.HIGH

        discrepancy = Discrepancy(
            discrepancy_id=self._generate_id(),
            discrepancy_type=DiscrepancyType.UNMATCHED_TRANSACTION,
            severity=severity,
            transaction_id=transaction_id,
            description=f"Transaction {transaction_id} has {len(field_differences)} field mismatch(es)",
            source_system=source_system,
            target_system=target_system,
            details={
                'source_transaction': source_details,
                'target_transaction': target_details,
                'field_differences': field_differences,
                'mismatched_fields': [d['field'] for d in field_differences]
            }
        )

        self.discrepancies.append(discrepancy)
        self.unmatched_transactions.append(discrepancy)

        fields_str = ", ".join([d['field'] for d in field_differences])
        logger.warning(
            f"UNMATCHED TRANSACTION: {transaction_id} | "
            f"Mismatched fields: {fields_str} | Severity: {severity.value}"
        )

        return discrepancy

    def add_duplicate_record(
        self,
        transaction_id: str,
        system: str,
        occurrence_count: int,
        transaction_details: Dict[str, Any],
        all_occurrences: List[Dict[str, Any]],
        severity: Severity = Severity.HIGH
    ) -> Discrepancy:
        """
        Record a duplicate record discrepancy.
        Same transaction appears multiple times in a system.
        """
        discrepancy = Discrepancy(
            discrepancy_id=self._generate_id(),
            discrepancy_type=DiscrepancyType.DUPLICATE_RECORD,
            severity=severity,
            transaction_id=transaction_id,
            description=f"Transaction {transaction_id} appears {occurrence_count} times in {system}",
            source_system=system,
            target_system=system,
            details={
                'occurrence_count': occurrence_count,
                'primary_transaction': transaction_details,
                'all_occurrences': all_occurrences,
                'duplicate_count': occurrence_count - 1
            }
        )

        self.discrepancies.append(discrepancy)
        self.duplicate_records.append(discrepancy)

        logger.warning(
            f"DUPLICATE RECORD: {transaction_id} | "
            f"Appears {occurrence_count} times in {system} | "
            f"Amount: {transaction_details.get('amount', 'N/A')} {transaction_details.get('currency', '')}"
        )

        return discrepancy

    def add_count_discrepancy(
        self,
        source_system: str,
        target_system: str,
        source_count: int,
        target_count: int,
        category: str = "total",
        severity: Severity = Severity.MEDIUM
    ) -> Discrepancy:
        """
        Record a count-level discrepancy.
        Total or category counts don't match between systems.
        """
        difference = abs(source_count - target_count)
        percentage_diff = (difference / max(source_count, 1)) * 100

        # Upgrade severity based on magnitude
        if percentage_diff > 10:
            severity = Severity.HIGH
        if percentage_diff > 25:
            severity = Severity.CRITICAL

        discrepancy = Discrepancy(
            discrepancy_id=self._generate_id(),
            discrepancy_type=DiscrepancyType.COUNT_DISCREPANCY,
            severity=severity,
            transaction_id=None,
            description=f"{category.title()} count mismatch: {source_count} vs {target_count}",
            source_system=source_system,
            target_system=target_system,
            details={
                'category': category,
                'source_count': source_count,
                'target_count': target_count,
                'difference': difference,
                'percentage_difference': round(percentage_diff, 2),
                'more_in': source_system if source_count > target_count else target_system
            }
        )

        self.discrepancies.append(discrepancy)
        self.count_discrepancies.append(discrepancy)

        logger.warning(
            f"COUNT DISCREPANCY: {category.title()} | "
            f"{source_system}: {source_count}, {target_system}: {target_count} | "
            f"Difference: {difference} ({percentage_diff:.1f}%)"
        )

        return discrepancy

    def get_exception_list(self) -> List[Dict]:
        """
        Generate an exception list of all discrepancies.
        Sorted by severity (CRITICAL first) then by timestamp.
        """
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3
        }

        sorted_discrepancies = sorted(
            self.discrepancies,
            key=lambda d: (severity_order[d.severity], d.timestamp)
        )

        return [d.to_dict() for d in sorted_discrepancies]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all tracked discrepancies."""
        return {
            'run_id': self.run_id,
            'total_discrepancies': len(self.discrepancies),
            'by_type': {
                'missing_records': len(self.missing_records),
                'unmatched_transactions': len(self.unmatched_transactions),
                'duplicate_records': len(self.duplicate_records),
                'count_discrepancies': len(self.count_discrepancies)
            },
            'by_severity': {
                'critical': sum(1 for d in self.discrepancies if d.severity == Severity.CRITICAL),
                'high': sum(1 for d in self.discrepancies if d.severity == Severity.HIGH),
                'medium': sum(1 for d in self.discrepancies if d.severity == Severity.MEDIUM),
                'low': sum(1 for d in self.discrepancies if d.severity == Severity.LOW)
            }
        }

    def save_to_file(self, filepath: str = None) -> str:
        """Save all discrepancies to a JSON file."""
        if filepath is None:
            project_root = Path(__file__).parent.parent
            discrepancy_dir = project_root / "data" / "discrepancies"
            discrepancy_dir.mkdir(parents=True, exist_ok=True)
            filepath = discrepancy_dir / f"discrepancies_{self.run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output = {
            'run_id': self.run_id,
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'exception_list': self.get_exception_list()
        }

        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"Discrepancies saved to: {filepath}")
        return str(filepath)