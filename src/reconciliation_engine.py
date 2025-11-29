"""
Reconciliation Engine
Compares payment platform transactions with compliance system transactions
and identifies discrepancies.

Tracks and logs:
- Missing records
- Unmatched transactions
- Duplicate records
- Count-level discrepancies

Each run logs:
- Timestamp
- Volume comparison
- Record-level discrepancies
- Exception list
- Confirmation of success or failure
"""

import json
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime

try:
    from .logger_config import setup_logger, get_logger
    from .discrepancy_tracker import DiscrepancyTracker, Severity
    from .run_logger import ReconciliationRunLogger
except ImportError:
    from logger_config import setup_logger, get_logger
    from discrepancy_tracker import DiscrepancyTracker, Severity
    from run_logger import ReconciliationRunLogger

# Initialize logger
logger = setup_logger("reconciliation")


class ReconciliationEngine:
    def __init__(self, payment_txns: List[Dict], compliance_txns: List[Dict], run_id: str = None):
        self.payment_txns = payment_txns
        self.compliance_txns = compliance_txns
        self.payment_txn_map = {txn['transaction_id']: txn for txn in payment_txns}
        self.compliance_txn_map = defaultdict(list)

        # Initialize tracking components
        self.run_logger = ReconciliationRunLogger(run_id)
        self.discrepancy_tracker = DiscrepancyTracker(self.run_logger.run_id)
        self.run_logger.set_discrepancy_tracker(self.discrepancy_tracker)

        # Group compliance transactions by transaction_id
        for txn in compliance_txns:
            self.compliance_txn_map[txn['transaction_id']].append(txn)

        logger.info(f"ReconciliationEngine initialized with {len(payment_txns)} payment and {len(compliance_txns)} compliance transactions")

    def find_missing_transactions(self) -> List[Dict]:
        """Find transactions in payment platform but missing in compliance"""
        missing = []

        for txn_id, payment_txn in self.payment_txn_map.items():
            if txn_id not in self.compliance_txn_map:
                missing.append({
                    'transaction_id': txn_id,
                    'message_type': payment_txn['message_type'],
                    'amount': payment_txn['amount'],
                    'currency': payment_txn['currency'],
                    'value_date': payment_txn['value_date'],
                    'payment_details': payment_txn,
                    'issue': 'Missing in compliance system',
                    'severity': 'HIGH'
                })

        return missing

    def find_duplicate_transactions(self) -> List[Dict]:
        """Find transactions that appear multiple times in compliance system"""
        duplicates = []

        for txn_id, compliance_txn_list in self.compliance_txn_map.items():
            if len(compliance_txn_list) > 1:
                # This transaction appears multiple times
                if txn_id in self.payment_txn_map:
                    payment_txn = self.payment_txn_map[txn_id]
                    duplicates.append({
                        'transaction_id': txn_id,
                        'message_type': payment_txn['message_type'],
                        'amount': payment_txn['amount'],
                        'currency': payment_txn['currency'],
                        'value_date': payment_txn['value_date'],
                        'occurrence_count': len(compliance_txn_list),
                        'payment_details': payment_txn,
                        'compliance_details': compliance_txn_list,
                        'issue': f'Appears {len(compliance_txn_list)} times in compliance system',
                        'severity': 'HIGH'
                    })

        return duplicates

    def compare_transaction_fields(self, payment_txn: Dict, compliance_txn: Dict) -> List[Dict]:
        """Compare individual fields between payment and compliance transactions"""
        differences = []

        # Common fields to compare
        common_fields = ['amount', 'currency', 'value_date']

        for field in common_fields:
            if field in payment_txn and field in compliance_txn:
                payment_value = str(payment_txn[field])
                compliance_value = str(compliance_txn[field])

                if payment_value != compliance_value:
                    differences.append({
                        'field': field,
                        'payment_value': payment_value,
                        'compliance_value': compliance_value
                    })

        # Message type specific comparisons
        msg_type = payment_txn.get('message_type')

        if msg_type == 'pacs.008':
            specific_fields = ['debtor_name', 'debtor_account', 'creditor_name', 'creditor_account', 'end_to_end_id']
        elif msg_type == 'pacs.009':
            specific_fields = ['instructing_agent', 'instructed_agent', 'end_to_end_id']
        elif msg_type == 'MT103':
            specific_fields = ['ordering_customer', 'beneficiary_customer', 'transaction_reference']
        elif msg_type == 'MT202':
            specific_fields = ['ordering_institution', 'beneficiary_institution', 'transaction_reference']
        else:
            specific_fields = []

        for field in specific_fields:
            if field in payment_txn and field in compliance_txn:
                if payment_txn[field] != compliance_txn[field]:
                    differences.append({
                        'field': field,
                        'payment_value': str(payment_txn[field]),
                        'compliance_value': str(compliance_txn[field])
                    })

        return differences

    def find_transactions_with_differences(self) -> List[Dict]:
        """Find transactions that exist in both systems but have differences"""
        discrepancies = []

        for txn_id, payment_txn in self.payment_txn_map.items():
            if txn_id in self.compliance_txn_map:
                compliance_txn_list = self.compliance_txn_map[txn_id]

                # Only check the first occurrence for differences
                # (duplicates are handled separately)
                compliance_txn = compliance_txn_list[0]

                differences = self.compare_transaction_fields(payment_txn, compliance_txn)

                if differences:
                    # Determine severity based on type of difference
                    severity = 'MEDIUM'
                    if any(diff['field'] in ['amount', 'currency'] for diff in differences):
                        severity = 'HIGH'

                    discrepancies.append({
                        'transaction_id': txn_id,
                        'message_type': payment_txn['message_type'],
                        'amount': payment_txn['amount'],
                        'currency': payment_txn['currency'],
                        'value_date': payment_txn['value_date'],
                        'differences': differences,
                        'payment_details': payment_txn,
                        'compliance_details': compliance_txn,
                        'issue': f'{len(differences)} field(s) mismatch',
                        'severity': severity
                    })

        return discrepancies

    def run_reconciliation(self, save_logs: bool = True) -> Dict:
        """
        Run full reconciliation and return all discrepancies.

        Logs:
        - Timestamp
        - Volume comparison
        - Record-level discrepancies (Missing, Unmatched, Duplicates, Count discrepancies)
        - Exception list
        - Confirmation of success or failure

        Args:
            save_logs: If True, saves run logs and discrepancy files

        Returns:
            Dictionary containing reconciliation results
        """
        logger.info("Starting reconciliation process...")

        try:
            # Find discrepancies
            missing = self.find_missing_transactions()
            duplicates = self.find_duplicate_transactions()
            differences = self.find_transactions_with_differences()

            total_payment_txns = len(self.payment_txns)
            total_compliance_txns = len(self.compliance_txns)
            matched_txns = total_payment_txns - len(missing) - len(differences)

            # Track Missing Records
            for item in missing:
                self.discrepancy_tracker.add_missing_record(
                    transaction_id=item['transaction_id'],
                    source_system="Payment Platform",
                    target_system="Compliance System",
                    transaction_details=item['payment_details'],
                    severity=Severity.HIGH
                )

            # Track Duplicate Records
            for item in duplicates:
                self.discrepancy_tracker.add_duplicate_record(
                    transaction_id=item['transaction_id'],
                    system="Compliance System",
                    occurrence_count=item['occurrence_count'],
                    transaction_details=item['payment_details'],
                    all_occurrences=item['compliance_details'],
                    severity=Severity.HIGH
                )

            # Track Unmatched Transactions (field mismatches)
            for item in differences:
                severity = Severity.HIGH if item['severity'] == 'HIGH' else Severity.MEDIUM
                self.discrepancy_tracker.add_unmatched_transaction(
                    transaction_id=item['transaction_id'],
                    source_system="Payment Platform",
                    target_system="Compliance System",
                    source_details=item['payment_details'],
                    target_details=item['compliance_details'],
                    field_differences=item['differences'],
                    severity=severity
                )

            # Track Count-level Discrepancies
            if total_payment_txns != total_compliance_txns:
                self.discrepancy_tracker.add_count_discrepancy(
                    source_system="Payment Platform",
                    target_system="Compliance System",
                    source_count=total_payment_txns,
                    target_count=total_compliance_txns,
                    category="total_transactions"
                )

            # Log volume comparison
            self.run_logger.log_volume_comparison(
                source_system="Payment Platform",
                target_system="Compliance System",
                source_total=total_payment_txns,
                target_total=total_compliance_txns,
                matched_count=matched_txns
            )

            # Log discrepancy summary
            self.run_logger.log_discrepancy_summary()

            # Log exception list
            self.run_logger.log_exception_list()

            # Build results
            results = {
                'summary': {
                    'run_id': self.run_logger.run_id,
                    'total_payment_transactions': total_payment_txns,
                    'total_compliance_transactions': total_compliance_txns,
                    'matched_transactions': matched_txns,
                    'missing_in_compliance': len(missing),
                    'transactions_with_differences': len(differences),
                    'duplicate_transactions': len(duplicates),
                    'reconciliation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'discrepancy_summary': self.discrepancy_tracker.get_summary()
                },
                'missing_transactions': missing,
                'duplicate_transactions': duplicates,
                'transactions_with_differences': differences,
                'exception_list': self.discrepancy_tracker.get_exception_list()
            }

            # Complete the run successfully
            self.run_logger.complete_run(success=True)

            # Save logs if requested
            if save_logs:
                self.run_logger.save_run_log()
                self.discrepancy_tracker.save_to_file()

            return results

        except Exception as e:
            logger.error(f"Reconciliation failed with error: {str(e)}")
            self.run_logger.complete_run(success=False, error_message=str(e))
            if save_logs:
                self.run_logger.save_run_log()
            raise


def load_transactions():
    """Load transaction data from JSON files"""
    from pathlib import Path
    base_dir = Path(__file__).parent.parent / 'data'

    with open(base_dir / 'payment_platform_transactions.json', 'r') as f:
        payment_txns = json.load(f)

    with open(base_dir / 'compliance_transactions.json', 'r') as f:
        compliance_txns = json.load(f)

    return payment_txns, compliance_txns


def save_reconciliation_results(results: Dict):
    """Save reconciliation results to JSON"""
    from pathlib import Path
    base_dir = Path(__file__).parent.parent / 'data'

    with open(base_dir / 'reconciliation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to reconciliation_results.json")


if __name__ == '__main__':
    payment_txns, compliance_txns = load_transactions()
    engine = ReconciliationEngine(payment_txns, compliance_txns)
    results = engine.run_reconciliation()
    save_reconciliation_results(results)
