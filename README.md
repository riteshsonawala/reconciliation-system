# Transaction Reconciliation System

A compliance-focused reconciliation system that compares payment platform transactions (CHAPS and cross-border payments) with compliance system records to identify discrepancies.

## Overview

This system helps compliance teams ensure that nothing goes out of the bank without being properly screened by identifying:

1. **Missing Transactions**: Transactions present in the payment platform but missing in the compliance system
2. **Transactions with Differences**: Transactions that exist in both systems but have field-level discrepancies
3. **Duplicate Transactions**: Transactions that appear multiple times in the compliance system

## Features

- Support for multiple payment message types:
  - **pacs.008**: Customer Credit Transfer
  - **pacs.009**: Financial Institution Credit Transfer
  - **MT 103**: Single Customer Credit Transfer
  - **MT 202**: General Financial Institution Transfer

- Interactive Streamlit UI with:
  - Dashboard overview with key metrics
  - Detailed views for each discrepancy type
  - Filtering by message type, currency, and severity
  - Field-by-field comparison for transactions with differences
  - Export capabilities

- Docker containerization for easy deployment

## Project Structure

```
reconciliation-system/
├── data/                                    # Transaction data files
│   ├── payment_platform_transactions.json   # Payment platform data
│   ├── compliance_transactions.json         # Compliance system data
│   └── reconciliation_results.json          # Reconciliation results
├── scripts/
│   └── generate_dummy_data.py              # Generate test transaction data
├── src/
│   ├── reconciliation_engine.py            # Core reconciliation logic
│   └── streamlit_app.py                    # Streamlit UI application
├── Dockerfile                              # Docker configuration
├── docker-compose.yml                      # Docker Compose configuration
├── requirements.txt                        # Python dependencies
└── README.md                               # This file
```

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- OR Python 3.11+ (for local development)

### Option 1: Running with Docker (Recommended)

1. **Navigate to the project directory:**
   ```bash
   cd ~/Projects/reconciliation-system
   ```

2. **Build and run the container:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   Open your browser and navigate to: `http://localhost:8501`

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Option 2: Running Locally

1. **Navigate to the project directory:**
   ```bash
   cd ~/Projects/reconciliation-system
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Streamlit app:**
   ```bash
   streamlit run src/streamlit_app.py
   ```

5. **Access the application:**
   Open your browser and navigate to: `http://localhost:8501`

## Usage

### Generating New Test Data

The project comes with pre-generated dummy data (300 transactions). To regenerate new test data:

```bash
python scripts/generate_dummy_data.py
```

This will create:
- 300 payment platform transactions (75 of each message type)
- Approximately 307 compliance transactions with various scenarios:
  - ~60% matching transactions
  - ~15% missing in compliance
  - ~15% with field differences
  - ~10% duplicates in compliance

### Running Reconciliation

The reconciliation runs automatically when you open the Streamlit app. To run it manually:

```bash
python src/reconciliation_engine.py
```

This will generate a `reconciliation_results.json` file with detailed findings.

### Using the Web Interface

1. **Dashboard View**: Overview of all reconciliation metrics and issue counts

2. **Missing Transactions**:
   - View all transactions in payment platform but missing in compliance
   - Filter by message type and currency
   - View detailed transaction information

3. **Duplicate Transactions**:
   - View all transactions appearing multiple times in compliance
   - See occurrence count for each duplicate
   - Compare payment platform data with compliance duplicates

4. **Transactions with Differences**:
   - View all transactions with field-level discrepancies
   - Filter by severity (HIGH/MEDIUM/LOW)
   - See field-by-field comparison
   - View complete transaction details side-by-side

### Simulating Daily Batch Process

To simulate the daily batch process that queries CHAPS and cross-border payments:

```bash
# Regenerate data (simulating new day's transactions)
python scripts/generate_dummy_data.py

# Run reconciliation
python src/reconciliation_engine.py

# View results in UI or check reconciliation_results.json
```

## Transaction Details

### Payment Platform Formats

Each message type contains specific fields:

**pacs.008 (Customer Credit Transfer):**
- Debtor and creditor information
- Account numbers and BIC codes
- Remittance information

**pacs.009 (Financial Institution Credit Transfer):**
- Instructing and instructed agents
- Settlement methods
- Purpose codes

**MT 103 (Single Customer Credit Transfer):**
- Ordering customer and institution
- Beneficiary customer and institution
- Sender to receiver information

**MT 202 (General Financial Institution Transfer):**
- Ordering and beneficiary institutions
- Correspondent information
- Related references

### Compliance System Format

Compliance transactions are stored in key-value format with:
- Common fields: transaction_id, message_type, amount, currency, value_date
- Message-specific fields extracted from payment platform

## Severity Levels

- **HIGH**: Critical issues like missing transactions or amount/currency mismatches
- **MEDIUM**: Field-level differences in account numbers or names
- **LOW**: Minor discrepancies in non-critical fields

## Development

### Adding New Message Types

1. Add generator function in `generate_dummy_data.py`
2. Update `transaction_to_compliance_format()` method
3. Update field comparison logic in `reconciliation_engine.py`

### Customizing Scenarios

Edit weights in `generate_dummy_data.py`:
```python
scenario = random.choices(
    ['match', 'missing', 'difference', 'duplicate'],
    weights=[60, 15, 15, 10]  # Adjust these weights
)[0]
```

## Docker Commands

```bash
# Build the image
docker-compose build

# Start the container
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down

# Rebuild and start
docker-compose up --build

# Remove all containers and volumes
docker-compose down -v
```

## Troubleshooting

### Port Already in Use

If port 8501 is already in use, edit `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Change 8502 to any available port
```

### Data Not Updating

1. Regenerate data: `python scripts/generate_dummy_data.py`
2. Click "Refresh Data" button in the Streamlit sidebar

### Docker Permission Issues

On Linux, you may need to run Docker commands with `sudo` or add your user to the docker group:
```bash
sudo usermod -aG docker $USER
```

## Future Enhancements

- Database integration for persistent storage
- Email alerts for high-severity discrepancies
- Automated daily scheduling
- Export to CSV/Excel
- Audit trail and logging
- User authentication and role-based access
- Integration with actual payment platforms
- Real-time reconciliation

## License

This project is for internal compliance use.

## Support

For questions or issues, please contact the compliance team.
