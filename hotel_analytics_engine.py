from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class RoomRecord:
    room_id: str
    room_type: str
    price_per_night: float
    room_status: str


@dataclass
class BookingResult:
    booking_id: str
    room_id: str
    guest_id: str
    checkin_date: str
    nights: int
    booking_status: str
    revenue: float
    error_message: str


def _is_valid_date(date_value: str) -> bool:
    try:
        datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def load_rooms(rooms_csv_path: str | Path) -> Dict[str, RoomRecord]:
    rooms: Dict[str, RoomRecord] = {}
    with open(rooms_csv_path, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            room = RoomRecord(
                room_id=row["room_id"],
                room_type=row["room_type"],
                price_per_night=float(row["price_per_night"]),
                room_status=row["room_status"],
            )
            rooms[room.room_id] = room
    return rooms


def _reject(
    booking_id: str,
    room_id: str,
    guest_id: str,
    checkin_date: str,
    nights: int,
    error_message: str,
) -> BookingResult:
    return BookingResult(
        booking_id=booking_id,
        room_id=room_id,
        guest_id=guest_id,
        checkin_date=checkin_date,
        nights=nights,
        booking_status="REJECTED",
        revenue=0.0,
        error_message=error_message,
    )


def process_bookings(
    rooms_csv_path: str | Path,
    bookings_csv_path: str | Path,
) -> Tuple[List[BookingResult], List[dict], dict]:
    rooms = load_rooms(rooms_csv_path)
    booking_results: List[BookingResult] = []
    cancellation_counts: Dict[str, int] = {}

    valid_checkin_dates: List[datetime] = []

    with open(bookings_csv_path, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            booking_id = row["booking_id"]
            room_id = row["room_id"]
            guest_id = row["guest_id"]
            checkin_date = row["checkin_date"]
            raw_status = row["booking_status"].strip().upper()

            if raw_status == "CANCELLED":
                cancellation_counts[room_id] = cancellation_counts.get(room_id, 0) + 1

            try:
                nights = int(row["nights"])
            except (TypeError, ValueError):
                booking_results.append(
                    _reject(
                        booking_id,
                        room_id,
                        guest_id,
                        checkin_date,
                        0,
                        "nights must be greater than 0",
                    )
                )
                continue

            if room_id not in rooms:
                booking_results.append(
                    _reject(
                        booking_id,
                        room_id,
                        guest_id,
                        checkin_date,
                        nights,
                        "Room does not exist",
                    )
                )
                continue

            room = rooms[room_id]

            if room.room_status != "AVAILABLE":
                booking_results.append(
                    _reject(
                        booking_id,
                        room_id,
                        guest_id,
                        checkin_date,
                        nights,
                        "Room is under maintenance",
                    )
                )
                continue

            if not _is_valid_date(checkin_date):
                booking_results.append(
                    _reject(
                        booking_id,
                        room_id,
                        guest_id,
                        checkin_date,
                        nights,
                        "Invalid checkin_date",
                    )
                )
                continue

            if nights <= 0:
                booking_results.append(
                    _reject(
                        booking_id,
                        room_id,
                        guest_id,
                        checkin_date,
                        nights,
                        "nights must be greater than 0",
                    )
                )
                continue

            valid_checkin_dates.append(datetime.strptime(checkin_date, "%Y-%m-%d"))

            if raw_status == "CANCELLED":
                booking_results.append(
                    BookingResult(
                        booking_id=booking_id,
                        room_id=room_id,
                        guest_id=guest_id,
                        checkin_date=checkin_date,
                        nights=nights,
                        booking_status="CANCELLED",
                        revenue=0.0,
                        error_message="",
                    )
                )
                continue

            revenue = nights * room.price_per_night
            booking_results.append(
                BookingResult(
                    booking_id=booking_id,
                    room_id=room_id,
                    guest_id=guest_id,
                    checkin_date=checkin_date,
                    nights=nights,
                    booking_status="CONFIRMED",
                    revenue=revenue,
                    error_message="",
                )
            )

    occupancy_rows = _build_occupancy_summary(rooms, booking_results, valid_checkin_dates)
    cancellation_analysis = _build_cancellation_analysis(cancellation_counts)

    return booking_results, occupancy_rows, cancellation_analysis


def _build_occupancy_summary(
    rooms: Dict[str, RoomRecord],
    booking_results: List[BookingResult],
    valid_checkin_dates: List[datetime],
) -> List[dict]:
    if not valid_checkin_dates:
        return []

    period_start = min(valid_checkin_dates)
    period_end = max(valid_checkin_dates)
    period_days = (period_end - period_start).days + 1

    rooms_by_type: Dict[str, List[RoomRecord]] = {}
    for room in rooms.values():
        if room.room_status == "AVAILABLE":
            rooms_by_type.setdefault(room.room_type, []).append(room)

    occupied_nights_by_type: Dict[str, int] = {
        room_type: 0 for room_type in rooms_by_type
    }

    for result in booking_results:
        if result.booking_status != "CONFIRMED":
            continue
        room = rooms[result.room_id]
        occupied_nights_by_type[room.room_type] += result.nights

    summary_rows: List[dict] = []
    for room_type in sorted(rooms_by_type):
        total_rooms = len(rooms_by_type[room_type])
        occupied_nights = occupied_nights_by_type[room_type]
        available_room_nights = total_rooms * period_days
        occupancy_rate = (
            round((occupied_nights / available_room_nights) * 100, 2)
            if available_room_nights
            else 0.0
        )
        summary_rows.append(
            {
                "room_type": room_type,
                "total_rooms": total_rooms,
                "period_days": period_days,
                "occupied_nights": occupied_nights,
                "available_room_nights": available_room_nights,
                "occupancy_rate": occupancy_rate,
            }
        )

    return summary_rows


def _build_cancellation_analysis(
    cancellation_counts: Dict[str, int],
) -> dict:
    flagged_rooms = [
        {
            "room_id": room_id,
            "cancellation_count": count,
        }
        for room_id, count in sorted(cancellation_counts.items())
        if count > 3
    ]
    flagged_rooms.sort(key=lambda item: (-item["cancellation_count"], item["room_id"]))

    return {
        "total_cancellations": sum(cancellation_counts.values()),
        "cancellations_by_room": dict(
            sorted(cancellation_counts.items(), key=lambda item: item[0])
        ),
        "flagged_rooms": flagged_rooms,
    }


def write_booking_revenue_report(
    booking_results: List[BookingResult], output_path: str | Path
) -> None:
    fieldnames = [
        "booking_id",
        "room_id",
        "guest_id",
        "checkin_date",
        "nights",
        "booking_status",
        "revenue",
        "error_message",
    ]
    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in booking_results:
            writer.writerow(
                {
                    "booking_id": result.booking_id,
                    "room_id": result.room_id,
                    "guest_id": result.guest_id,
                    "checkin_date": result.checkin_date,
                    "nights": result.nights,
                    "booking_status": result.booking_status,
                    "revenue": result.revenue,
                    "error_message": result.error_message,
                }
            )


def write_room_occupancy_summary(
    occupancy_rows: List[dict], output_path: str | Path
) -> None:
    fieldnames = [
        "room_type",
        "total_rooms",
        "period_days",
        "occupied_nights",
        "available_room_nights",
        "occupancy_rate",
    ]
    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(occupancy_rows)


def write_cancellation_analysis(
    cancellation_analysis: dict, output_path: str | Path
) -> None:
    with open(output_path, mode="w", encoding="utf-8") as jsonfile:
        json.dump(cancellation_analysis, jsonfile, indent=2)


def run_engine(
    rooms_csv_path: str | Path = "hotel_rooms.csv",
    bookings_csv_path: str | Path = "hotel_bookings.csv",
    revenue_report_path: str | Path = "booking_revenue_report.csv",
    occupancy_summary_path: str | Path = "room_occupancy_summary.csv",
    cancellation_analysis_path: str | Path = "cancellation_analysis.json",
) -> Tuple[List[BookingResult], List[dict], dict]:
    booking_results, occupancy_rows, cancellation_analysis = process_bookings(
        rooms_csv_path, bookings_csv_path
    )
    write_booking_revenue_report(booking_results, revenue_report_path)
    write_room_occupancy_summary(occupancy_rows, occupancy_summary_path)
    write_cancellation_analysis(cancellation_analysis, cancellation_analysis_path)
    return booking_results, occupancy_rows, cancellation_analysis


if __name__ == "__main__":
    run_engine()
