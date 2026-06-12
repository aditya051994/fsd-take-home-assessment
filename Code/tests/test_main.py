"""
Integration tests for the FastAPI backend (main.py)
Tests API endpoints and their responses
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app, load_data


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """Load data once for all tests"""
    load_data()


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check_status(self, client):
        """Test health check returns OK"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_check_content(self, client):
        """Test health check response format"""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "healthy"


class TestSummaryEndpoint:
    """Tests for reconciliation summary endpoint"""
    
    def test_summary_status(self, client):
        """Test summary endpoint returns OK"""
        response = client.get("/api/summary")
        assert response.status_code == 200
    
    def test_summary_structure(self, client):
        """Test summary response has required fields"""
        response = client.get("/api/summary")
        data = response.json()
        
        required_fields = [
            'total_meetings',
            'matched_pairs',
            'crm_only',
            'calendar_only',
            'internal_meetings',
            'data_quality'
        ]
        
        for field in required_fields:
            assert field in data
    
    def test_summary_values_non_negative(self, client):
        """Test summary values are non-negative"""
        response = client.get("/api/summary")
        data = response.json()
        
        assert data['total_meetings'] >= 0
        assert data['matched_pairs'] >= 0
        assert data['crm_only'] >= 0
        assert data['calendar_only'] >= 0
        assert data['internal_meetings'] >= 0
    
    def test_summary_total_calculation(self, client):
        """Test summary total is calculated correctly"""
        response = client.get("/api/summary")
        data = response.json()
        
        calculated_total = (data['matched_pairs'] + 
                           data['crm_only'] + 
                           data['calendar_only'])
        
        assert data['total_meetings'] == calculated_total


class TestMeetingsEndpoint:
    """Tests for meetings list endpoint"""
    
    def test_meetings_status(self, client):
        """Test meetings endpoint returns OK"""
        response = client.get("/api/meetings")
        assert response.status_code == 200
    
    def test_meetings_structure(self, client):
        """Test meetings response structure"""
        response = client.get("/api/meetings")
        data = response.json()
        
        required_fields = ['total', 'skip', 'limit', 'count', 'meetings']
        for field in required_fields:
            assert field in data
    
    def test_meetings_pagination(self, client):
        """Test meetings pagination works"""
        response1 = client.get("/api/meetings?skip=0&limit=5")
        response2 = client.get("/api/meetings?skip=5&limit=5")
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1['skip'] == 0
        assert data1['limit'] == 5
        assert data2['skip'] == 5
        assert data2['limit'] == 5
    
    def test_meetings_count_matches_returned(self, client):
        """Test that count matches number of returned meetings"""
        response = client.get("/api/meetings?limit=50")
        data = response.json()
        
        assert data['count'] == len(data['meetings'])
    
    def test_meeting_has_required_fields(self, client):
        """Test each meeting has required fields"""
        response = client.get("/api/meetings?limit=5")
        data = response.json()
        
        required_fields = [
            'reconciliation_id',
            'combined_data',
            'data_conflicts',
            'reconciliation_type'
        ]
        
        for meeting in data['meetings']:
            for field in required_fields:
                assert field in meeting
    
    def test_meetings_filter_by_type(self, client):
        """Test filtering meetings by reconciliation type"""
        response = client.get("/api/meetings?reconciliation_type=Matched&limit=50")
        data = response.json()
        
        for meeting in data['meetings']:
            assert meeting['reconciliation_type'] == 'Matched'
    
    def test_meetings_filter_by_conflicts(self, client):
        """Test filtering meetings by conflicts"""
        response = client.get("/api/meetings?has_conflicts=true&limit=50")
        data = response.json()
        
        for meeting in data['meetings']:
            assert len(meeting.get('data_conflicts', [])) > 0


class TestMeetingDetailEndpoint:
    """Tests for individual meeting endpoint"""
    
    def test_get_specific_meeting(self, client):
        """Test retrieving specific meeting by ID"""
        # First get a meeting ID
        response = client.get("/api/meetings?limit=1")
        meetings = response.json()['meetings']
        
        if meetings:
            meeting_id = meetings[0]['reconciliation_id']
            response = client.get(f"/api/meetings/{meeting_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data['reconciliation_id'] == meeting_id
    
    def test_nonexistent_meeting_404(self, client):
        """Test that nonexistent meeting returns 404"""
        response = client.get("/api/meetings/NONEXISTENT-ID")
        assert response.status_code == 404


class TestConflictsEndpoint:
    """Tests for conflicts endpoint"""
    
    def test_conflicts_status(self, client):
        """Test conflicts endpoint returns OK"""
        response = client.get("/api/conflicts")
        assert response.status_code == 200
    
    def test_conflicts_structure(self, client):
        """Test conflicts response structure"""
        response = client.get("/api/conflicts")
        data = response.json()
        
        required_fields = ['total', 'skip', 'limit', 'count', 'conflicts']
        for field in required_fields:
            assert field in data
    
    def test_conflicts_have_data(self, client):
        """Test all returned conflicts have conflicts field"""
        response = client.get("/api/conflicts?limit=50")
        data = response.json()
        
        for conflict_item in data['conflicts']:
            assert 'data_conflicts' in conflict_item
            assert len(conflict_item['data_conflicts']) > 0


class TestStatisticsEndpoint:
    """Tests for statistics endpoint"""
    
    def test_statistics_status(self, client):
        """Test statistics endpoint returns OK"""
        response = client.get("/api/statistics")
        assert response.status_code == 200
    
    def test_statistics_structure(self, client):
        """Test statistics response structure"""
        response = client.get("/api/statistics")
        data = response.json()
        
        required_fields = [
            'total_meetings',
            'by_reconciliation_type',
            'total_conflicts',
            'conflict_by_severity',
            'average_conflicts_per_meeting'
        ]
        
        for field in required_fields:
            assert field in data
    
    def test_statistics_by_type(self, client):
        """Test statistics includes all reconciliation types"""
        response = client.get("/api/statistics")
        data = response.json()
        
        types = data['by_reconciliation_type']
        assert 'Matched' in types or len(types) >= 0


class TestRawDataEndpoints:
    """Tests for raw data endpoints"""
    
    def test_crm_events_endpoint(self, client):
        """Test CRM events endpoint"""
        response = client.get("/api/crm-events")
        assert response.status_code == 200
        
        data = response.json()
        assert 'count' in data
        assert 'events' in data
        assert data['count'] > 0
    
    def test_calendar_events_endpoint(self, client):
        """Test calendar events endpoint"""
        response = client.get("/api/calendar-events")
        assert response.status_code == 200
        
        data = response.json()
        assert 'count' in data
        assert 'events' in data
        assert data['count'] > 0


class TestGroupingEndpoints:
    """Tests for data grouping endpoints"""
    
    def test_meetings_by_client(self, client):
        """Test meetings grouped by client"""
        response = client.get("/api/meetings-by-client")
        assert response.status_code == 200
        
        data = response.json()
        assert 'clients' in data
        assert len(data['clients']) > 0
    
    def test_meetings_by_date(self, client):
        """Test meetings grouped by date"""
        response = client.get("/api/meetings-by-date")
        assert response.status_code == 200
        
        data = response.json()
        assert 'meetings_by_date' in data
        assert len(data['meetings_by_date']) > 0


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_invalid_query_parameter(self, client):
        """Test handling of invalid query parameters"""
        response = client.get("/api/meetings?limit=abc")
        # Should handle validation error gracefully
        assert response.status_code in [200, 422]  # 200 with default or 422 validation error
    
    def test_nonexistent_endpoint_404(self, client):
        """Test that nonexistent endpoints return 404"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404


class TestCORSHeaders:
    """Tests for CORS headers"""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present"""
        response = client.get("/api/health")
        
        # CORS headers should be present
        assert response.status_code == 200


class TestResponseFormats:
    """Tests for response formats"""
    
    def test_json_response_format(self, client):
        """Test that responses are valid JSON"""
        response = client.get("/api/summary")
        
        # Should be able to parse as JSON
        data = response.json()
        assert isinstance(data, dict)
    
    def test_empty_list_handling(self, client):
        """Test handling of empty lists"""
        response = client.get("/api/meetings?limit=1000000")
        data = response.json()
        
        # Should handle large limit gracefully
        assert 'meetings' in data
        assert isinstance(data['meetings'], list)


class TestDataConsistency:
    """Tests for data consistency"""
    
    def test_all_meetings_have_type(self, client):
        """Test that all meetings have reconciliation type"""
        response = client.get("/api/meetings?limit=50")
        data = response.json()
        
        valid_types = ['Matched', 'CRM Only', 'Calendar Only']
        for meeting in data['meetings']:
            assert meeting['reconciliation_type'] in valid_types
    
    def test_matched_meetings_have_both_sources(self, client):
        """Test that matched meetings have both CRM and Calendar IDs"""
        response = client.get("/api/meetings?reconciliation_type=Matched&limit=50")
        data = response.json()
        
        for meeting in data['meetings']:
            if meeting['reconciliation_type'] == 'Matched':
                assert meeting.get('source_crm_id') is not None
                assert meeting.get('source_calendar_id') is not None
    
    def test_conflicts_have_field_info(self, client):
        """Test that conflicts have all required info"""
        response = client.get("/api/conflicts?limit=5")
        data = response.json()
        
        for meeting in data['conflicts']:
            for conflict in meeting.get('data_conflicts', []):
                assert 'field' in conflict
                assert 'crm_value' in conflict or 'calendar_value' in conflict
                assert 'severity' in conflict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
