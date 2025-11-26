"""
Streamlit UI for Transaction Reconciliation System
Displays discrepancies between payment platform and compliance system

Shows:
- Missing records
- Unmatched transactions
- Duplicate records
- Count-level discrepancies
- Exception list with severity
- Run logs with timestamps and success/failure status
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from reconciliation_engine import ReconciliationEngine, load_transactions

# Page configuration
st.set_page_config(
    page_title="Transaction Reconciliation System",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .severity-high {
        color: #d32f2f;
        font-weight: bold;
    }
    .severity-medium {
        color: #f57c00;
        font-weight: bold;
    }
    .severity-low {
        color: #388e3c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_reconciliation_results():
    """Load or generate reconciliation results"""
    try:
        payment_txns, compliance_txns = load_transactions()
        engine = ReconciliationEngine(payment_txns, compliance_txns)
        results = engine.run_reconciliation()
        return results
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


def display_summary(summary):
    """Display reconciliation summary metrics"""
    st.markdown('<p class="main-header">📊 Reconciliation Dashboard</p>', unsafe_allow_html=True)

    st.markdown(f"**Reconciliation Date:** {summary['reconciliation_date']}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Payment Txns", summary['total_payment_transactions'])

    with col2:
        st.metric("Total Compliance Txns", summary['total_compliance_transactions'])

    with col3:
        st.metric("✅ Matched", summary['matched_transactions'])

    with col4:
        total_issues = (summary['missing_in_compliance'] +
                       summary['transactions_with_differences'] +
                       summary['duplicate_transactions'])
        st.metric("⚠️ Total Issues", total_issues)

    st.markdown("---")

    # Issue breakdown
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🚫 Missing in Compliance")
        st.markdown(f"<h2 style='color: #d32f2f;'>{summary['missing_in_compliance']}</h2>",
                   unsafe_allow_html=True)

    with col2:
        st.markdown("### 🔄 With Differences")
        st.markdown(f"<h2 style='color: #f57c00;'>{summary['transactions_with_differences']}</h2>",
                   unsafe_allow_html=True)

    with col3:
        st.markdown("### 📑 Duplicates")
        st.markdown(f"<h2 style='color: #f57c00;'>{summary['duplicate_transactions']}</h2>",
                   unsafe_allow_html=True)


def display_missing_transactions(missing_txns):
    """Display transactions missing in compliance system"""
    st.markdown("---")
    st.markdown("## 🚫 Transactions Missing in Compliance System")

    if not missing_txns:
        st.success("No missing transactions found!")
        return

    st.warning(f"Found {len(missing_txns)} transactions in payment platform that are missing in compliance system.")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        msg_types = ['All'] + sorted(list(set([txn['message_type'] for txn in missing_txns])))
        selected_type = st.selectbox("Filter by Message Type", msg_types, key='missing_type')

    with col2:
        currencies = ['All'] + sorted(list(set([txn['currency'] for txn in missing_txns])))
        selected_currency = st.selectbox("Filter by Currency", currencies, key='missing_currency')

    # Apply filters
    filtered_txns = missing_txns
    if selected_type != 'All':
        filtered_txns = [txn for txn in filtered_txns if txn['message_type'] == selected_type]
    if selected_currency != 'All':
        filtered_txns = [txn for txn in filtered_txns if txn['currency'] == selected_currency]

    # Display as table
    if filtered_txns:
        df = pd.DataFrame([{
            'Transaction ID': txn['transaction_id'],
            'Type': txn['message_type'],
            'Amount': f"{txn['amount']:,.2f}",
            'Currency': txn['currency'],
            'Value Date': txn['value_date'],
            'Severity': txn['severity']
        } for txn in filtered_txns])

        st.dataframe(df, use_container_width=True)

        # Expandable details
        with st.expander("View Detailed Transaction Information"):
            selected_txn_id = st.selectbox(
                "Select Transaction ID",
                [txn['transaction_id'] for txn in filtered_txns],
                key='missing_detail'
            )

            selected_txn = next((txn for txn in filtered_txns if txn['transaction_id'] == selected_txn_id), None)
            if selected_txn:
                st.json(selected_txn['payment_details'])
    else:
        st.info("No transactions match the selected filters.")


def display_duplicate_transactions(duplicate_txns):
    """Display duplicate transactions in compliance system"""
    st.markdown("---")
    st.markdown("## 📑 Duplicate Transactions in Compliance System")

    if not duplicate_txns:
        st.success("No duplicate transactions found!")
        return

    st.warning(f"Found {len(duplicate_txns)} transactions that appear multiple times in compliance system.")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        msg_types = ['All'] + sorted(list(set([txn['message_type'] for txn in duplicate_txns])))
        selected_type = st.selectbox("Filter by Message Type", msg_types, key='dup_type')

    with col2:
        currencies = ['All'] + sorted(list(set([txn['currency'] for txn in duplicate_txns])))
        selected_currency = st.selectbox("Filter by Currency", currencies, key='dup_currency')

    # Apply filters
    filtered_txns = duplicate_txns
    if selected_type != 'All':
        filtered_txns = [txn for txn in filtered_txns if txn['message_type'] == selected_type]
    if selected_currency != 'All':
        filtered_txns = [txn for txn in filtered_txns if txn['currency'] == selected_currency]

    # Display as table
    if filtered_txns:
        df = pd.DataFrame([{
            'Transaction ID': txn['transaction_id'],
            'Type': txn['message_type'],
            'Amount': f"{txn['amount']:,.2f}",
            'Currency': txn['currency'],
            'Value Date': txn['value_date'],
            'Occurrences': txn['occurrence_count'],
            'Severity': txn['severity']
        } for txn in filtered_txns])

        st.dataframe(df, use_container_width=True)

        # Expandable details
        with st.expander("View Detailed Transaction Information"):
            selected_txn_id = st.selectbox(
                "Select Transaction ID",
                [txn['transaction_id'] for txn in filtered_txns],
                key='dup_detail'
            )

            selected_txn = next((txn for txn in filtered_txns if txn['transaction_id'] == selected_txn_id), None)
            if selected_txn:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Payment Platform Data:**")
                    st.json(selected_txn['payment_details'])
                with col2:
                    st.markdown(f"**Compliance System Data ({selected_txn['occurrence_count']} occurrences):**")
                    st.json(selected_txn['compliance_details'])
    else:
        st.info("No transactions match the selected filters.")


def display_transactions_with_differences(diff_txns):
    """Display transactions with field differences"""
    st.markdown("---")
    st.markdown("## 🔄 Transactions with Differences")

    if not diff_txns:
        st.success("No transactions with differences found!")
        return

    st.warning(f"Found {len(diff_txns)} transactions with discrepancies between payment platform and compliance system.")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        msg_types = ['All'] + sorted(list(set([txn['message_type'] for txn in diff_txns])))
        selected_type = st.selectbox("Filter by Message Type", msg_types, key='diff_type')

    with col2:
        currencies = ['All'] + sorted(list(set([txn['currency'] for txn in diff_txns])))
        selected_currency = st.selectbox("Filter by Currency", currencies, key='diff_currency')

    with col3:
        severities = ['All', 'HIGH', 'MEDIUM', 'LOW']
        selected_severity = st.selectbox("Filter by Severity", severities, key='diff_severity')

    # Apply filters
    filtered_txns = diff_txns
    if selected_type != 'All':
        filtered_txns = [txn for txn in filtered_txns if txn['message_type'] == selected_type]
    if selected_currency != 'All':
        filtered_txns = [txn for txn in filtered_txns if txn['currency'] == selected_currency]
    if selected_severity != 'All':
        filtered_txns = [txn for txn in filtered_txns if txn['severity'] == selected_severity]

    # Display as table
    if filtered_txns:
        df = pd.DataFrame([{
            'Transaction ID': txn['transaction_id'],
            'Type': txn['message_type'],
            'Amount': f"{txn['amount']:,.2f}",
            'Currency': txn['currency'],
            'Value Date': txn['value_date'],
            'Issue': txn['issue'],
            'Severity': txn['severity']
        } for txn in filtered_txns])

        st.dataframe(df, use_container_width=True)

        # Expandable details
        with st.expander("View Field-by-Field Comparison"):
            selected_txn_id = st.selectbox(
                "Select Transaction ID",
                [txn['transaction_id'] for txn in filtered_txns],
                key='diff_detail'
            )

            selected_txn = next((txn for txn in filtered_txns if txn['transaction_id'] == selected_txn_id), None)
            if selected_txn:
                st.markdown(f"**Transaction:** {selected_txn['transaction_id']} ({selected_txn['message_type']})")

                # Show differences in a table
                diff_df = pd.DataFrame([{
                    'Field': diff['field'],
                    'Payment Platform': diff['payment_value'],
                    'Compliance System': diff['compliance_value'],
                    'Match': '❌'
                } for diff in selected_txn['differences']])

                st.dataframe(diff_df, use_container_width=True)

                # Show full details
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Complete Payment Platform Data:**")
                    st.json(selected_txn['payment_details'])
                with col2:
                    st.markdown("**Complete Compliance System Data:**")
                    st.json(selected_txn['compliance_details'])
    else:
        st.info("No transactions match the selected filters.")


def display_exception_list(exception_list, summary):
    """Display the exception list with all discrepancies sorted by severity"""
    st.markdown("---")
    st.markdown("## Exception List")

    if not exception_list:
        st.success("No exceptions found - all records reconciled successfully!")
        return

    st.warning(f"Found {len(exception_list)} exceptions requiring review")

    # Summary by severity
    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for exc in exception_list:
        severity = exc.get('severity', 'MEDIUM')
        if severity in severity_counts:
            severity_counts[severity] += 1

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("CRITICAL", severity_counts['CRITICAL'])
    with col2:
        st.metric("HIGH", severity_counts['HIGH'])
    with col3:
        st.metric("MEDIUM", severity_counts['MEDIUM'])
    with col4:
        st.metric("LOW", severity_counts['LOW'])

    st.markdown("---")

    # Filter by type
    disc_types = ['All'] + sorted(list(set([exc.get('discrepancy_type', 'unknown') for exc in exception_list])))
    selected_type = st.selectbox("Filter by Discrepancy Type", disc_types, key='exc_type')

    # Filter by severity
    severities = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    selected_severity = st.selectbox("Filter by Severity", severities, key='exc_severity')

    filtered_exceptions = exception_list
    if selected_type != 'All':
        filtered_exceptions = [exc for exc in filtered_exceptions if exc.get('discrepancy_type') == selected_type]
    if selected_severity != 'All':
        filtered_exceptions = [exc for exc in filtered_exceptions if exc.get('severity') == selected_severity]

    if filtered_exceptions:
        df = pd.DataFrame([{
            'ID': exc.get('discrepancy_id', 'N/A'),
            'Type': exc.get('discrepancy_type', 'N/A').replace('_', ' ').title(),
            'Severity': exc.get('severity', 'N/A'),
            'Transaction': exc.get('transaction_id', 'N/A'),
            'Description': exc.get('description', 'N/A'),
            'Timestamp': exc.get('timestamp', 'N/A')
        } for exc in filtered_exceptions])

        st.dataframe(df, use_container_width=True)

        # Detailed view
        with st.expander("View Exception Details"):
            exc_ids = [exc.get('discrepancy_id', 'N/A') for exc in filtered_exceptions]
            selected_exc = st.selectbox("Select Exception ID", exc_ids, key='exc_detail')

            selected = next((exc for exc in filtered_exceptions if exc.get('discrepancy_id') == selected_exc), None)
            if selected:
                st.json(selected)
    else:
        st.info("No exceptions match the selected filters.")


def display_run_log(summary):
    """Display run log information"""
    st.markdown("---")
    st.markdown("## Run Log")

    run_id = summary.get('run_id', 'N/A')
    recon_date = summary.get('reconciliation_date', 'N/A')

    # Run metadata
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Run Information")
        st.markdown(f"**Run ID:** `{run_id}`")
        st.markdown(f"**Timestamp:** {recon_date}")

    with col2:
        st.markdown("### Volume Comparison")
        st.markdown(f"**Payment Platform:** {summary.get('total_payment_transactions', 0)} records")
        st.markdown(f"**Compliance System:** {summary.get('total_compliance_transactions', 0)} records")
        volume_diff = abs(summary.get('total_payment_transactions', 0) - summary.get('total_compliance_transactions', 0))
        st.markdown(f"**Volume Difference:** {volume_diff}")

    st.markdown("---")

    # Record-level discrepancies
    st.markdown("### Record-Level Discrepancies")

    disc_summary = summary.get('discrepancy_summary', {})

    if disc_summary:
        by_type = disc_summary.get('by_type', {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Missing Records", by_type.get('missing_records', 0))
        with col2:
            st.metric("Unmatched Transactions", by_type.get('unmatched_transactions', 0))
        with col3:
            st.metric("Duplicate Records", by_type.get('duplicate_records', 0))
        with col4:
            st.metric("Count Discrepancies", by_type.get('count_discrepancies', 0))

        st.markdown("---")

        # Severity breakdown
        st.markdown("### Severity Breakdown")
        by_severity = disc_summary.get('by_severity', {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("CRITICAL", by_severity.get('critical', 0))
        with col2:
            st.metric("HIGH", by_severity.get('high', 0))
        with col3:
            st.metric("MEDIUM", by_severity.get('medium', 0))
        with col4:
            st.metric("LOW", by_severity.get('low', 0))
    else:
        st.info("No detailed discrepancy summary available.")

    st.markdown("---")

    # Status
    total_issues = (summary.get('missing_in_compliance', 0) +
                   summary.get('transactions_with_differences', 0) +
                   summary.get('duplicate_transactions', 0))

    st.markdown("### Run Status")
    if total_issues == 0:
        st.success("COMPLETED SUCCESS - All records reconciled without discrepancies")
    else:
        st.warning(f"COMPLETED WITH {total_issues} DISCREPANCIES - Review required")


def main():
    """Main application"""
    st.sidebar.title("Reconciliation System")
    st.sidebar.markdown("---")

    # Refresh button
    if st.sidebar.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigation")
    view = st.sidebar.radio(
        "Select View",
        ["Dashboard", "Missing Transactions", "Duplicate Transactions", "Transactions with Differences", "Exception List", "Run Log"]
    )

    # Load data
    results = load_reconciliation_results()

    if results is None:
        st.error("Failed to load reconciliation results.")
        return

    # Display based on selection
    if view == "Dashboard":
        display_summary(results['summary'])
        st.markdown("---")
        st.markdown("### Quick Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### Missing Transactions")
            st.metric("Count", len(results['missing_transactions']))
            if results['missing_transactions']:
                total_amount = sum(txn['amount'] for txn in results['missing_transactions'])
                st.metric("Total Amount", f"${total_amount:,.2f}")

        with col2:
            st.markdown("#### Duplicate Transactions")
            st.metric("Count", len(results['duplicate_transactions']))
            if results['duplicate_transactions']:
                total_amount = sum(txn['amount'] for txn in results['duplicate_transactions'])
                st.metric("Total Amount", f"${total_amount:,.2f}")

        with col3:
            st.markdown("#### Transactions with Differences")
            st.metric("Count", len(results['transactions_with_differences']))
            if results['transactions_with_differences']:
                high_severity = len([t for t in results['transactions_with_differences'] if t['severity'] == 'HIGH'])
                st.metric("High Severity", high_severity)

    elif view == "Missing Transactions":
        display_summary(results['summary'])
        display_missing_transactions(results['missing_transactions'])

    elif view == "Duplicate Transactions":
        display_summary(results['summary'])
        display_duplicate_transactions(results['duplicate_transactions'])

    elif view == "Transactions with Differences":
        display_summary(results['summary'])
        display_transactions_with_differences(results['transactions_with_differences'])

    elif view == "Exception List":
        display_summary(results['summary'])
        display_exception_list(results.get('exception_list', []), results['summary'])

    elif view == "Run Log":
        display_summary(results['summary'])
        display_run_log(results['summary'])

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This reconciliation system compares payment platform transactions "
        "(CHAPS, cross-border payments) with compliance system records to identify discrepancies."
    )


if __name__ == '__main__':
    main()
