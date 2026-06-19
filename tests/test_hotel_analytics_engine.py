import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hotel_analytics_engine import (
    process_bookings,
    run_engine,
    write_booking_revenue_report,
    write_cancellation_analysis,
    write_room_occupancy_summary,
)


class TestHotelAnalyticsEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        cls.rooms_path = base_dir / "hotel_rooms.csv"
        cls.bookings_path = base_dir / "hotel_bookings.csv"
        cls.booking_results, cls.occupancy_rows, cls.cancellation_analysis = (
            process_bookings(cls.rooms_path, cls.bookings_path)
        )
        cls.results_by_booking_id = {
            result.booking_id: result for result in cls.booking_results
        }
        cls.occupancy_by_type = {
            row["room_type"]: row for row in cls.occupancy_rows
        }

    def test_invalid_room_rejected(self) -> None:
        result = self.results_by_booking_id["BK006"]
        self.assertEqual(result.booking_status, "REJECTED")
        self.assertIn("Room does not exist", result.error_message)
        self.assertEqual(result.revenue, 0.0)

    def test_room_under_maintenance_rejected(self) -> None:
        result = self.results_by_booking_id["BK015"]
        self.assertEqual(result.booking_status, "REJECTED")
        self.assertIn("Room is under maintenance", result.error_message)
        self.assertEqual(result.revenue, 0.0)

    def test_invalid_date_rejected(self) -> None:
        result = self.results_by_booking_id["BK011"]
        self.assertEqual(result.booking_status, "REJECTED")
        self.assertIn("Invalid checkin_date", result.error_message)
        self.assertEqual(result.revenue, 0.0)

    def test_negative_nights_rejected(self) -> None:
        result = self.results_by_booking_id["BK016"]
        self.assertEqual(result.booking_status, "REJECTED")
        self.assertIn("nights must be greater than 0", result.error_message)
        self.assertEqual(result.revenue, 0.0)

    def test_revenue_calculation(self) -> None:
        result = self.results_by_booking_id["BK001"]
        self.assertEqual(result.booking_status, "CONFIRMED")
        self.assertEqual(result.nights, 2)
        self.assertEqual(result.revenue, 5000.0)

    def test_cancellation_exclusion(self) -> None:
        result = self.results_by_booking_id["BK014"]
        self.assertEqual(result.booking_status, "CANCELLED")
        self.assertEqual(result.revenue, 0.0)

    def test_occupancy_calculation(self) -> None:
        self.assertEqual(len(self.occupancy_rows), 3)
        deluxe = self.occupancy_by_type["DELUXE"]
        suite = self.occupancy_by_type["SUITE"]
        standard = self.occupancy_by_type["STANDARD"]

        self.assertEqual(deluxe["total_rooms"], 9)
        self.assertEqual(suite["total_rooms"], 9)
        self.assertEqual(standard["total_rooms"], 9)
        self.assertEqual(deluxe["period_days"], 25)
        self.assertEqual(deluxe["available_room_nights"], 225)
        self.assertEqual(deluxe["occupied_nights"], 61)
        self.assertEqual(deluxe["occupancy_rate"], 27.11)
        self.assertEqual(suite["occupied_nights"], 54)
        self.assertEqual(suite["occupancy_rate"], 24.0)
        self.assertEqual(standard["occupied_nights"], 57)
        self.assertEqual(standard["occupancy_rate"], 25.33)

    def test_cancellation_analysis(self) -> None:
        self.assertEqual(self.cancellation_analysis["total_cancellations"], 10)
        self.assertEqual(self.cancellation_analysis["cancellations_by_room"]["RM015"], 1)
        self.assertEqual(self.cancellation_analysis["flagged_rooms"], [])

        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            rooms_path = temp / "hotel_rooms.csv"
            bookings_path = temp / "hotel_bookings.csv"

            rooms_path.write_text(
                "room_id,room_type,price_per_night,room_status\n"
                "RM100,DELUXE,1000,AVAILABLE\n",
                encoding="utf-8",
            )
            bookings_path.write_text(
                "booking_id,room_id,guest_id,checkin_date,nights,booking_status\n"
                "BK100,RM100,G1,2025-08-01,1,CANCELLED\n"
                "BK101,RM100,G2,2025-08-02,1,CANCELLED\n"
                "BK102,RM100,G3,2025-08-03,1,CANCELLED\n"
                "BK103,RM100,G4,2025-08-04,1,CANCELLED\n"
                "BK104,RM100,G5,2025-08-05,1,CANCELLED\n",
                encoding="utf-8",
            )

            _, _, analysis = process_bookings(rooms_path, bookings_path)
            self.assertEqual(analysis["total_cancellations"], 5)
            self.assertEqual(len(analysis["flagged_rooms"]), 1)
            self.assertEqual(analysis["flagged_rooms"][0]["room_id"], "RM100")
            self.assertEqual(analysis["flagged_rooms"][0]["cancellation_count"], 5)

    def test_report_writers_and_run_engine(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            rooms_path = temp / "hotel_rooms.csv"
            bookings_path = temp / "hotel_bookings.csv"
            revenue_report_path = temp / "booking_revenue_report.csv"
            occupancy_summary_path = temp / "room_occupancy_summary.csv"
            cancellation_analysis_path = temp / "cancellation_analysis.json"

            rooms_path.write_text(
                "room_id,room_type,price_per_night,room_status\n"
                "RM200,STANDARD,500,AVAILABLE\n",
                encoding="utf-8",
            )
            bookings_path.write_text(
                "booking_id,room_id,guest_id,checkin_date,nights,booking_status\n"
                "BK200,RM200,G200,2025-09-01,3,CONFIRMED\n",
                encoding="utf-8",
            )

            booking_results, occupancy_rows, cancellation_analysis = run_engine(
                rooms_path,
                bookings_path,
                revenue_report_path,
                occupancy_summary_path,
                cancellation_analysis_path,
            )
            self.assertEqual(booking_results[0].booking_status, "CONFIRMED")
            self.assertEqual(booking_results[0].revenue, 1500.0)
            self.assertEqual(occupancy_rows[0]["occupied_nights"], 3)
            self.assertTrue(revenue_report_path.exists())
            self.assertTrue(occupancy_summary_path.exists())
            self.assertTrue(cancellation_analysis_path.exists())

            with open(cancellation_analysis_path, encoding="utf-8") as jsonfile:
                payload = json.load(jsonfile)
            self.assertEqual(payload["total_cancellations"], 0)

            write_booking_revenue_report(booking_results, temp / "revenue_2.csv")
            write_room_occupancy_summary(occupancy_rows, temp / "occupancy_2.csv")
            write_cancellation_analysis(
                cancellation_analysis, temp / "cancellation_2.json"
            )
            self.assertTrue((temp / "revenue_2.csv").exists())
            self.assertTrue((temp / "occupancy_2.csv").exists())
            self.assertTrue((temp / "cancellation_2.json").exists())


if __name__ == "__main__":
    unittest.main()
