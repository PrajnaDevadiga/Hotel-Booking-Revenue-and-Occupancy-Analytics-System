# 🏨 Hotel Booking Revenue & Occupancy Analytics System

A comprehensive Python-based analytical engine and interactive web dashboard designed to process hotel room inventories and booking records. The system computes financial performance, room occupancy rates, and cancellation risk, and visualizes them on a modern, high-fidelity Streamlit dashboard.

---

## 📂 Project Structure

```text
User Story24/
│
├── hotel_analytics_engine.py      # Core data processing, validation, and analytics engine
├── dashboard_app.py              # Premium Streamlit interactive visualization dashboard
│
├── hotel_rooms.csv               # Input: Master list of hotel room configurations
├── hotel_bookings.csv            # Input: Transactional log of bookings
│
├── booking_revenue_report.csv    # Output: Processed booking status, revenue, & validation logs
├── room_occupancy_summary.csv    # Output: Calculated occupancy metrics per room type
├── cancellation_analysis.json    # Output: JSON cancellation metrics and flagged high-risk rooms
│
├── requirements.txt              # Project dependencies
└── tests/
    └── test_hotel_analytics_engine.py   # Comprehensive unit test suite for the analytics engine
```

---

## 🛠️ Features

### 1. **Hotel Analytics Engine** (`hotel_analytics_engine.py`)
* **Booking Validation**: Automatically validates data and handles edge cases, classifying records as `CONFIRMED`, `CANCELLED`, or `REJECTED`.
* **Robust Error Handling**: Flags and rejects bookings with reasons such as:
  * Room does not exist in inventory.
  * Room is under maintenance.
  * Invalid/unparseable check-in dates.
  * Non-positive values for duration (nights $\le$ 0).
* **Metrics Compilation**:
  * Calculates revenue (nights $\times$ price per night) for confirmed bookings.
  * Computes room occupancy rates over the booking date range per room type.
  * Profiles cancellation counts, flagging rooms with more than 3 cancellations.

### 2. **Interactive Streamlit Dashboard** (`dashboard_app.py`)
* **Executive Overview (KPIs)**: High-level cards for Total Bookings, Total Revenue, Occupancy Rate, Cancellations, Active Rooms, and Risk Rooms.
* **Revenue Performance**: Line charts (Daily & Cumulative), bar charts of revenue by room type, and contribution breakdown.
* **Room Occupancy Analytics**: Horizontal bar charts, occupancy utilization gauge with risk levels, and a calendar heatmap highlighting booking patterns by weekday.
* **Booking Volume & Status**: Status distribution pie charts, cumulative volume area charts, and daily check-in trendlines.
* **Cancellation Risk Profiles**: Room-type cancellation rates and flagged risk list.
* **Data Quality & Validation**: Deep-dive audit trail to inspect rejected bookings, showing invalid inputs and error messages.
* **Granular Filtering**: Search by Booking/Room ID, filter by check-in date range, room type, booking status, revenue threshold, and a dedicated **Drill-down Room Type Focus**.

---

## ⚙️ Setup & Installation

### Prerequisite
Ensure you have Python 3.8+ installed.

### 1. Clone & Navigate to Project Directory
```bash
cd "d:\UnifyCX Internship\User Story24"
```

### 2. Install Dependencies
Install the required packages using `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Note: Make sure to install `streamlit`, `pandas`, `numpy`, and `plotly` if they are not already installed globally:*
```bash
pip install streamlit pandas numpy plotly pytest pytest-cov
```

---

## 🚀 Running the Application

### 1. Execute the Analytics Engine
To process the raw CSV data and generate the output reports locally:
```bash
python hotel_analytics_engine.py
```
This reads `hotel_rooms.csv` and `hotel_bookings.csv` and writes the following report files to the root directory:
* `booking_revenue_report.csv`
* `room_occupancy_summary.csv`
* `cancellation_analysis.json`

### 2. Run the Streamlit Dashboard
Launch the interactive web-based dashboard:
```bash
streamlit run dashboard_app.py
```
After running, Streamlit will open a tab in your default web browser (typically at `http://localhost:8501`).

---

## 📊 Data Specifications

### Input Formats

#### 🔑 Rooms Master (`hotel_rooms.csv`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `room_id` | String | Unique identifier (e.g., `RM001`) |
| `room_type` | String | Room class (`STANDARD`, `DELUXE`, `SUITE`) |
| `price_per_night`| Numeric| Price of the room per night |
| `room_status` | String | Status (`AVAILABLE` or `MAINTENANCE`) |

#### 📅 Bookings Transactions (`hotel_bookings.csv`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `booking_id` | String | Unique identifier (e.g., `BK001`) |
| `room_id` | String | Target room identifier |
| `guest_id` | String | Unique guest identifier |
| `checkin_date` | String | Date of check-in (`YYYY-MM-DD`) |
| `nights` | Integer| Number of nights requested |
| `booking_status`| String | Status (`CONFIRMED`, `CANCELLED`) |

---

## 🧪 Running Unit Tests

A comprehensive unit test suite is provided to verify validation logic, calculations, and output report generation.

### Run Tests with Pytest
```bash
python -m pytest tests/ -v
```

### Run Tests with Coverage Report
To view the code coverage metrics for the analytical engine:
```bash
python -m pytest tests/ -v --cov=hotel_analytics_engine
```
