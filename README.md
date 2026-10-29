# Bus Ticket Analysis

An end-to-end data analytics portfolio project using Python and Power BI to explore booking trends, customer behavior, and bus transportation performance.

## Project Overview

This project simulates a bus ticket marketplace to analyze booking transactions, customer activity, route performance, and operator performance.

**Note:** All datasets are synthetic and generated for educational and portfolio purposes. They do not represent real transactions or actual customers.

## Objectives

- Analyze booking and revenue trends over time.
- Evaluate route and bus operator performance.
- Understand customer booking behavior and repeat purchases.
- Examine cancellations, refunds, voucher usage, and seat occupancy.
- Build an interactive Power BI dashboard to support data-driven decisions.

## Tools & Technologies

- Python
- Pandas
- NumPy
- Power BI
- DAX
- Data Modeling

## Repository Structure

- `data/`: Synthetic datasets in CSV format.
- `src/`: Python script for generating the datasets.
- `dashboard/`: Power BI dashboard.

## Dataset

The project contains eight tables:

**Dimension tables**
- `dim_date`
- `dim_route`
- `dim_operator`
- `dim_customer`
- `dim_channel`
- `dim_voucher`

**Fact tables**
- `fact_trips`
- `fact_bookings`

## Dashboard Preview

The dashboard preview will be added here after the report is finalized.

## How to Use

1. Clone or download this repository.
2. Install the required Python libraries using `pip install -r requirements.txt`.
3. Run the script in `src/` to generate the synthetic datasets.
4. Open the Power BI file in `dashboard/` using Power BI Desktop.

## Future Improvements

- Add customer retention and cohort analysis.
- Improve the data model and DAX measures.
- Expand the dashboard with additional business insights.
