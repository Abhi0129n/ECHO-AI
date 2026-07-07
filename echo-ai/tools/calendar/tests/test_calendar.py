import unittest
from datetime import datetime, timedelta
from tools.calendar.calendar_service import CalendarService
from tools.calendar.calendar_utils import validate_iso_format, find_free_slots

class TestCalendarService(unittest.TestCase):
    def setUp(self):
        self.service = CalendarService()

    def test_utils(self):
        self.assertTrue(validate_iso_format("2026-07-07T10:00:00"))
        self.assertTrue(validate_iso_format("2026-07-07T10:00:00Z"))
        self.assertFalse(validate_iso_format("invalid-time"))
        
        # Test Free Slots Finder
        start = datetime(2026, 7, 7, 9, 0, 0)
        end = datetime(2026, 7, 7, 12, 0, 0)
        busy = [
            (datetime(2026, 7, 7, 10, 0, 0), datetime(2026, 7, 7, 11, 0, 0))
        ]
        duration = timedelta(minutes=30)
        
        slots = find_free_slots(busy, start, end, duration)
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0], (start, busy[0][0]))
        self.assertEqual(slots[1], (busy[0][1], end))

    def test_service_list_events(self):
        events = self.service.today_events()
        self.assertTrue(len(events) > 0)
        self.assertEqual(events[0].id, "event1")
        self.assertEqual(events[0].summary, "Weekly Status Meeting")

    def test_service_search(self):
        res = self.service.search_events("Status")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, "event1")

    def test_service_create(self):
        from tools.calendar.calendar_models import CreateEventRequest
        req = CreateEventRequest(
            summary="Test Event",
            start_time="2026-07-07T18:00:00Z",
            end_time="2026-07-07T19:00:00Z"
        )
        created = self.service.create_event(req)
        self.assertEqual(created.id, "new_event_123")
        self.assertEqual(created.summary, "Test Event")

if __name__ == "__main__":
    unittest.main()
