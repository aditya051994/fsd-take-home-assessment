"""
Test fixtures and configuration for Event Sync Service tests
"""
import json
from pathlib import Path
import pytest


@pytest.fixture
def sample_crm_events():
    """Sample CRM events for testing"""
    return [
        {
            "crm_id": "CRM-1001",
            "subject": "Q1 Portfolio Review",
            "client_name": "David Park",
            "client_company": "Meridian Capital",
            "relationship_owner": "Sarah Chen",
            "meeting_date": "2025-03-10",
            "meeting_time": "14:00",
            "meeting_type": "In-Person",
            "location": "HQ - Conference Room B",
            "notes": "Review Q1 allocation strategy.",
            "status": "Completed",
            "created_at": "2025-02-28T09:15:00Z"
        },
        {
            "crm_id": "CRM-1002",
            "subject": "Portfolio Walkthrough",
            "client_name": "Mark Johnson",
            "client_company": "Summit Advisors",
            "relationship_owner": "Sarah Chen",
            "meeting_date": "2025-03-12",
            "meeting_time": "10:00",
            "meeting_type": "In-Person",
            "location": "NYC Office",
            "notes": "Walk through current portfolio.",
            "status": "Confirmed",
            "created_at": "2025-03-01T11:30:00Z"
        },
        {
            "crm_id": "CRM-1003",
            "subject": "Internal Meeting",
            "client_name": None,
            "client_company": None,
            "relationship_owner": "Sarah Chen",
            "meeting_date": "2025-03-14",
            "meeting_time": "16:00",
            "meeting_type": "Internal",
            "location": "HQ - Room 4A",
            "notes": "Internal review",
            "status": "Confirmed",
            "created_at": "2025-01-15T10:00:00Z"
        }
    ]


@pytest.fixture
def sample_calendar_events():
    """Sample calendar events for testing"""
    return [
        {
            "event_id": "CAL-A1",
            "title": "Q1 Portfolio Review - Meridian Capital",
            "organizer": "sarah.chen@firma.com",
            "attendees": ["sarah.chen@firma.com", "david.park@meridiancap.com"],
            "start_time": "2025-03-10T14:00:00",
            "end_time": "2025-03-10T15:30:00",
            "location": "Conference Room B",
            "description": "Quarterly review of portfolio allocation.",
            "is_recurring": False,
            "status": "confirmed",
            "created_at": "2025-02-27T10:00:00Z"
        },
        {
            "event_id": "CAL-A2",
            "title": "Summit Advisors - Portfolio Discussion",
            "organizer": "sarah.chen@firma.com",
            "attendees": ["sarah.chen@firma.com", "mark.johnson@summitadv.com"],
            "start_time": "2025-03-12T10:00:00",
            "end_time": "2025-03-12T11:00:00",
            "location": "Zoom Link",
            "description": "Portfolio walkthrough.",
            "is_recurring": False,
            "status": "confirmed",
            "created_at": "2025-02-28T15:45:00Z"
        },
        {
            "event_id": "CAL-A3",
            "title": "Unmatched Calendar Event",
            "organizer": "priya.sharma@firma.com",
            "attendees": [],
            "start_time": "2025-03-20T15:00:00",
            "end_time": "2025-03-20T16:00:00",
            "location": "Virtual",
            "description": "Some event",
            "is_recurring": False,
            "status": "tentative",
            "created_at": "2025-03-13T22:10:00Z"
        }
    ]


@pytest.fixture
def real_crm_data():
    """Load real CRM data from file"""
    crm_file = Path(__file__).parent.parent / "data" / "crm_events.json"
    if not crm_file.exists():
        pytest.skip("CRM data file not found")
    with open(crm_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def real_calendar_data():
    """Load real calendar data from file"""
    cal_file = Path(__file__).parent.parent / "data" / "calendar_events.json"
    if not cal_file.exists():
        pytest.skip("Calendar data file not found")
    with open(cal_file, 'r') as f:
        return json.load(f)
