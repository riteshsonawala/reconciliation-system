"""
Generate dummy transaction data for payment platform and compliance system.
Creates scenarios for testing reconciliation logic.
"""

import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
import xml.etree.ElementTree as ET
from xml.dom import minidom

class TransactionGenerator:
    def __init__(self):
        self.currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF']
        self.countries = ['US', 'GB', 'DE', 'FR', 'JP', 'CH', 'NL', 'IT']
        self.banks = [
            'CHASUS33XXX', 'DEUTDEFFXXX', 'HSBCGB2LXXX', 'BNPAFRPPXXX',
            'UBSWCHZHXXX', 'CITIUS33XXX', 'BARCGB22XXX', 'CRESCHZZXXX'
        ]
        self.company_names = [
            'Global Trading Ltd', 'Acme Corporation', 'TechVentures Inc',
            'International Exports SA', 'Finance Solutions GmbH', 'Trading Partners LLC',
            'Continental Industries', 'Worldwide Logistics', 'Premium Services Ltd'
        ]

    def generate_reference(self, prefix='TXN'):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = random.randint(1000, 9999)
        return f"{prefix}{timestamp}{random_suffix}"

    def generate_amount(self):
        return round(random.uniform(1000, 5000000), 2)

    def generate_date(self, days_back=0):
        base_date = datetime.now() - timedelta(days=days_back)
        return base_date.strftime('%Y-%m-%d')

    def generate_pacs008(self, txn_id, amount, currency):
        """Generate pacs.008 (Customer Credit Transfer)"""
        return {
            'message_type': 'pacs.008',
            'transaction_id': txn_id,
            'amount': amount,
            'currency': currency,
            'value_date': self.generate_date(),
            'debtor_name': random.choice(self.company_names),
            'debtor_account': f"GB{random.randint(10000000, 99999999):08d}{random.randint(10000000, 99999999):08d}",
            'debtor_bic': random.choice(self.banks),
            'creditor_name': random.choice(self.company_names),
            'creditor_account': f"GB{random.randint(10000000, 99999999):08d}{random.randint(10000000, 99999999):08d}",
            'creditor_bic': random.choice(self.banks),
            'remittance_info': f"Invoice payment {random.randint(1000, 9999)}",
            'instruction_id': self.generate_reference('INST'),
            'end_to_end_id': self.generate_reference('E2E')
        }

    def generate_pacs009(self, txn_id, amount, currency):
        """Generate pacs.009 (Financial Institution Credit Transfer)"""
        return {
            'message_type': 'pacs.009',
            'transaction_id': txn_id,
            'amount': amount,
            'currency': currency,
            'value_date': self.generate_date(),
            'instructing_agent': random.choice(self.banks),
            'instructed_agent': random.choice(self.banks),
            'creditor_institution': random.choice(self.banks),
            'debtor_institution': random.choice(self.banks),
            'settlement_method': 'CLRG',
            'instruction_id': self.generate_reference('INST'),
            'end_to_end_id': self.generate_reference('E2E'),
            'purpose': 'INTC'
        }

    def generate_mt103(self, txn_id, amount, currency):
        """Generate MT 103 (Single Customer Credit Transfer)"""
        return {
            'message_type': 'MT103',
            'transaction_id': txn_id,
            'transaction_reference': self.generate_reference('MT103'),
            'amount': amount,
            'currency': currency,
            'value_date': self.generate_date(),
            'ordering_customer': random.choice(self.company_names),
            'ordering_institution': random.choice(self.banks),
            'beneficiary_customer': random.choice(self.company_names),
            'beneficiary_institution': random.choice(self.banks),
            'intermediary_institution': random.choice(self.banks) if random.random() > 0.5 else None,
            'sender_to_receiver_info': f"Payment for services {random.randint(1000, 9999)}",
            'remittance_info': f"Invoice {random.randint(10000, 99999)}"
        }

    def generate_mt202(self, txn_id, amount, currency):
        """Generate MT 202 (General Financial Institution Transfer)"""
        return {
            'message_type': 'MT202',
            'transaction_id': txn_id,
            'transaction_reference': self.generate_reference('MT202'),
            'amount': amount,
            'currency': currency,
            'value_date': self.generate_date(),
            'ordering_institution': random.choice(self.banks),
            'beneficiary_institution': random.choice(self.banks),
            'sender_correspondent': random.choice(self.banks),
            'receiver_correspondent': random.choice(self.banks),
            'intermediary': random.choice(self.banks) if random.random() > 0.6 else None,
            'related_reference': self.generate_reference('REL')
        }

    def transaction_to_compliance_format(self, txn):
        """Convert payment platform transaction to compliance key-value format"""
        compliance_txn = {
            'transaction_id': txn['transaction_id'],
            'message_type': txn['message_type'],
            'amount': str(txn['amount']),
            'currency': txn['currency'],
            'value_date': txn['value_date'],
        }

        # Add message type specific fields
        if txn['message_type'] == 'pacs.008':
            compliance_txn.update({
                'debtor_name': txn['debtor_name'],
                'debtor_account': txn['debtor_account'],
                'creditor_name': txn['creditor_name'],
                'creditor_account': txn['creditor_account'],
                'end_to_end_id': txn['end_to_end_id']
            })
        elif txn['message_type'] == 'pacs.009':
            compliance_txn.update({
                'instructing_agent': txn['instructing_agent'],
                'instructed_agent': txn['instructed_agent'],
                'end_to_end_id': txn['end_to_end_id']
            })
        elif txn['message_type'] == 'MT103':
            compliance_txn.update({
                'ordering_customer': txn['ordering_customer'],
                'beneficiary_customer': txn['beneficiary_customer'],
                'transaction_reference': txn['transaction_reference']
            })
        elif txn['message_type'] == 'MT202':
            compliance_txn.update({
                'ordering_institution': txn['ordering_institution'],
                'beneficiary_institution': txn['beneficiary_institution'],
                'transaction_reference': txn['transaction_reference']
            })

        return compliance_txn

def generate_all_transactions():
    """Generate all transactions with different scenarios"""
    generator = TransactionGenerator()

    # Distribution: 75 each type
    pacs008_count = 75
    pacs009_count = 75
    mt103_count = 75
    mt202_count = 75

    payment_platform_txns = []
    compliance_txns = []

    txn_counter = 1

    # Generate each type of transaction
    message_types = [
        ('pacs.008', pacs008_count, generator.generate_pacs008),
        ('pacs.009', pacs009_count, generator.generate_pacs009),
        ('MT103', mt103_count, generator.generate_mt103),
        ('MT202', mt202_count, generator.generate_mt202)
    ]

    for msg_type, count, generator_func in message_types:
        for i in range(count):
            txn_id = f"TXN{txn_counter:06d}"
            amount = generator.generate_amount()
            currency = random.choice(generator.currencies)

            txn = generator_func(txn_id, amount, currency)
            payment_platform_txns.append(txn)

            # Scenario distribution for this transaction
            scenario = random.choices(
                ['match', 'missing', 'difference', 'duplicate'],
                weights=[60, 15, 15, 10]
            )[0]

            if scenario == 'match':
                # Perfect match
                compliance_txns.append(generator.transaction_to_compliance_format(txn))

            elif scenario == 'missing':
                # Transaction exists in payment platform but missing in compliance
                pass  # Don't add to compliance

            elif scenario == 'difference':
                # Transaction exists in both but with differences
                compliance_txn = generator.transaction_to_compliance_format(txn)

                # Introduce a random difference
                diff_type = random.choice(['amount', 'currency', 'name', 'account'])

                if diff_type == 'amount':
                    # Change amount slightly
                    compliance_txn['amount'] = str(float(compliance_txn['amount']) + random.uniform(-1000, 1000))
                elif diff_type == 'currency' and random.random() > 0.7:
                    # Change currency (less common)
                    compliance_txn['currency'] = random.choice([c for c in generator.currencies if c != txn['currency']])
                elif diff_type == 'name' and 'debtor_name' in compliance_txn:
                    compliance_txn['debtor_name'] = compliance_txn['debtor_name'] + ' LTD'
                elif diff_type == 'account' and 'debtor_account' in compliance_txn:
                    # Change one digit in account
                    acc = list(compliance_txn['debtor_account'])
                    acc[random.randint(0, len(acc)-1)] = str(random.randint(0, 9))
                    compliance_txn['debtor_account'] = ''.join(acc)

                compliance_txns.append(compliance_txn)

            elif scenario == 'duplicate':
                # Add transaction multiple times to compliance
                compliance_txn = generator.transaction_to_compliance_format(txn)
                num_duplicates = random.randint(2, 4)
                for _ in range(num_duplicates):
                    compliance_txns.append(compliance_txn.copy())

            txn_counter += 1

    return payment_platform_txns, compliance_txns

def save_transactions():
    """Generate and save transaction data"""
    payment_txns, compliance_txns = generate_all_transactions()

    # Save payment platform transactions
    with open('/Users/ritesh/Projects/reconciliation-system/data/payment_platform_transactions.json', 'w') as f:
        json.dump(payment_txns, f, indent=2)

    # Save compliance transactions
    with open('/Users/ritesh/Projects/reconciliation-system/data/compliance_transactions.json', 'w') as f:
        json.dump(compliance_txns, f, indent=2)

    print(f"Generated {len(payment_txns)} payment platform transactions")
    print(f"Generated {len(compliance_txns)} compliance transactions")
    print("\nScenario summary:")
    print(f"- Matching transactions: ~{int(len(payment_txns) * 0.6)}")
    print(f"- Missing in compliance: ~{int(len(payment_txns) * 0.15)}")
    print(f"- Transactions with differences: ~{int(len(payment_txns) * 0.15)}")
    print(f"- Duplicates in compliance: ~{int(len(payment_txns) * 0.10)}")

if __name__ == '__main__':
    save_transactions()
