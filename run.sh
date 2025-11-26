#!/bin/bash
# Quick start script for the reconciliation system

echo "========================================="
echo "Transaction Reconciliation System"
echo "========================================="
echo ""
echo "Select an option:"
echo "1. Generate new dummy data"
echo "2. Run reconciliation engine"
echo "3. Start Streamlit UI (local)"
echo "4. Run with Docker"
echo "5. Stop Docker containers"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "Generating new dummy data..."
        python scripts/generate_dummy_data.py
        ;;
    2)
        echo "Running reconciliation engine..."
        python src/reconciliation_engine.py
        ;;
    3)
        echo "Starting Streamlit UI..."
        streamlit run src/streamlit_app.py
        ;;
    4)
        echo "Building and starting Docker container..."
        docker-compose up --build
        ;;
    5)
        echo "Stopping Docker containers..."
        docker-compose down
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        ;;
esac
