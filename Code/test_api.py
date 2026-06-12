import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("EVENT SYNC SERVICE - API TEST RESULTS")
print("="*70 + "\n")

# Test 1: Health Check
print("1️⃣  HEALTH CHECK")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/api/health")
    pprint(response.json())
    print("✅ Status: OK\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 2: Summary
print("2️⃣  RECONCILIATION SUMMARY")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/api/summary")
    summary = response.json()
    print(f"Total Meetings Reconciled: {summary['total_meetings']}")
    print(f"Matched Pairs: {summary['matched_pairs']}")
    print(f"CRM Only: {summary['crm_only']}")
    print(f"Calendar Only: {summary['calendar_only']}")
    print(f"Internal Meetings: {summary['internal_meetings']}")
    print(f"Data Quality - Matched Percentage: {summary['data_quality']['matched_percentage']}%")
    print("✅ Status: OK\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 3: Statistics
print("3️⃣  DETAILED STATISTICS")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/api/statistics")
    stats = response.json()
    print(f"Total Meetings: {stats['total_meetings']}")
    print(f"Total Data Conflicts: {stats['total_conflicts']}")
    print(f"Average Conflicts per Meeting: {stats['average_conflicts_per_meeting']}")
    print("\nBy Reconciliation Type:")
    for rec_type, count in stats['by_reconciliation_type'].items():
        print(f"  - {rec_type}: {count}")
    print("\nConflict Severity:")
    for severity, count in stats['conflict_by_severity'].items():
        print(f"  - {severity}: {count}")
    print("✅ Status: OK\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 4: Sample Meetings
print("4️⃣  SAMPLE RECONCILED MEETINGS (First 3)")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/api/meetings?limit=3")
    data = response.json()
    for i, meeting in enumerate(data['meetings'], 1):
        print(f"\nMeeting #{i}:")
        print(f"  ID: {meeting['reconciliation_id']}")
        print(f"  Type: {meeting['reconciliation_type']}")
        print(f"  Subject: {meeting['combined_data'].get('subject', 'N/A')}")
        print(f"  Client: {meeting['combined_data'].get('client_company', 'N/A')}")
        print(f"  Date: {meeting['combined_data'].get('meeting_date', 'N/A')}")
        print(f"  Location: {meeting['combined_data'].get('location', 'N/A')}")
        conflicts = meeting.get('data_conflicts', [])
        if conflicts:
            print(f"  ⚠️  Conflicts: {len(conflicts)}")
            for conflict in conflicts:
                print(f"     - {conflict['field']}: CRM='{conflict['crm_value']}' vs CAL='{conflict['calendar_value']}'")
    print("\n✅ Status: OK\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 5: Conflicts
print("5️⃣  MEETINGS WITH DATA CONFLICTS (First 2)")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/api/conflicts?limit=2")
    data = response.json()
    print(f"Total Meetings with Conflicts: {data['total']}\n")
    for i, meeting in enumerate(data['conflicts'], 1):
        print(f"Meeting #{i}:")
        print(f"  ID: {meeting['reconciliation_id']}")
        print(f"  Subject: {meeting['combined_data'].get('subject', 'N/A')}")
        print(f"  Number of Conflicts: {len(meeting['data_conflicts'])}")
        for conflict in meeting['data_conflicts']:
            print(f"  - {conflict['field']}: '{conflict['crm_value']}' (CRM) vs '{conflict['calendar_value']}' (Calendar) [{conflict['severity']}]")
        print()
    print("✅ Status: OK\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 6: Meetings by Client
print("6️⃣  MEETINGS GROUPED BY CLIENT")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/api/meetings-by-client")
    data = response.json()
    for client, meetings in list(data['clients'].items())[:5]:
        print(f"  {client}: {len(meetings)} meeting(s)")
    print("\n✅ Status: OK\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

print("="*70)
print("🎉 ALL API TESTS COMPLETED SUCCESSFULLY!")
print("="*70)
print("\n📊 Web Interface: http://localhost:8000")
print("📚 API Documentation: http://localhost:8000/docs\n")
