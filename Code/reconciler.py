"""
Event Reconciliation Module
Matches meetings from CRM and Calendar sources based on multiple criteria
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher
import json


class EventReconciler:
    """Reconciles events from CRM and Calendar sources"""
    
    def __init__(self, crm_events: List[Dict], calendar_events: List[Dict]):
        self.crm_events = crm_events
        self.calendar_events = calendar_events
        self.matched_pairs: List[Tuple] = []
        self.unmatched_crm: List[Dict] = []
        self.unmatched_calendar: List[Dict] = []
        self.internal_events: List[Dict] = []
    
    def normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize various date formats to YYYY-MM-DD"""
        if not date_str:
            return None
        
        formats = [
            "%Y-%m-%d",
            "%m-%d/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return date_str
    
    def get_crm_datetime(self, crm_event: Dict) -> Optional[datetime]:
        """Extract datetime from CRM event"""
        try:
            date_str = self.normalize_date(crm_event.get("meeting_date"))
            time_str = crm_event.get("meeting_time")
            
            if not date_str:
                return None
            
            if time_str:
                dt_str = f"{date_str}T{time_str}:00"
            else:
                dt_str = f"{date_str}T00:00:00"
            
            return datetime.fromisoformat(dt_str)
        except Exception:
            return None
    
    def get_calendar_datetime(self, cal_event: Dict) -> Optional[datetime]:
        """Extract start datetime from calendar event"""
        try:
            start_time = cal_event.get("start_time")
            if start_time:
                # Handle Z timezone
                if start_time.endswith('Z'):
                    start_time = start_time[:-1]
                # Parse and make timezone-naive for comparison
                dt = datetime.fromisoformat(start_time)
                # If it has timezone info, convert to naive UTC
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
            return None
        except Exception:
            return None
    
    def similarity_score(self, str1: str, str2: str) -> float:
        """Calculate string similarity score 0-1"""
        if not str1 or not str2:
            return 0
        str1 = str(str1).lower().strip()
        str2 = str(str2).lower().strip()
        return SequenceMatcher(None, str1, str2).ratio()
    
    def extract_name_from_email(self, email: str) -> str:
        """Extract name from email address"""
        if not email:
            return ""
        name_part = email.split('@')[0].replace('.', ' ')
        return name_part.lower()
    
    def extract_company_from_title(self, title: str) -> str:
        """Extract company name from calendar event title"""
        if not title:
            return ""
        # Remove common patterns
        title = title.lower()
        for pattern in [' - ', ' meeting', ' discussion', ' call', ' sync', ' review', ' pitch', ' prep']:
            if pattern in title:
                return title.split(pattern)[0].strip()
        return title.strip()
    
    def extract_attendee_companies(self, attendees: List[str]) -> List[str]:
        """Extract company names from attendee emails"""
        companies = []
        for email in attendees:
            if '@' in email:
                company_part = email.split('@')[1].split('.')[0]
                companies.append(company_part.lower())
        return companies
    
    def is_time_overlap(self, dt1: datetime, dt2: datetime, tolerance_hours: int = 2) -> bool:
        """Check if two datetimes are within tolerance"""
        if not dt1 or not dt2:
            return False
        diff = abs((dt1 - dt2).total_seconds() / 3600)
        return diff <= tolerance_hours
    
    def is_client_match(self, crm_event: Dict, cal_event: Dict) -> float:
        """Score how well clients match between CRM and calendar"""
        score = 0.0
        max_score = 0.0
        
        # Try to match by client name
        crm_client = crm_event.get("client_name", "")
        crm_company = crm_event.get("client_company", "")
        
        cal_title = cal_event.get("title", "")
        cal_attendees = cal_event.get("attendees", [])
        
        # Check if CRM client name appears in calendar title
        if crm_client:
            max_score += 1.0
            if crm_client.lower() in cal_title.lower():
                score += 1.0
        
        # Check if CRM company appears in calendar title
        if crm_company:
            max_score += 1.0
            if crm_company.lower() in cal_title.lower():
                score += 1.0
        
        # Check attendee company matches
        if crm_company:
            max_score += 1.0
            attendee_companies = self.extract_attendee_companies(cal_attendees)
            crm_company_lower = crm_company.lower().replace(" ", "")
            for company in attendee_companies:
                if crm_company_lower in company or company in crm_company_lower:
                    score += 1.0
                    break
        
        if max_score == 0:
            return 0.0
        return score / max_score
    
    def is_subject_match(self, crm_event: Dict, cal_event: Dict) -> float:
        """Score how well subjects/titles match"""
        crm_subject = crm_event.get("subject", "")
        cal_title = cal_event.get("title", "")
        
        if not crm_subject or not cal_title:
            return 0.0
        
        return self.similarity_score(crm_subject, cal_title)
    
    def try_match_event(self, crm_event: Dict, used_calendar_ids: set) -> Optional[Dict]:
        """Try to find matching calendar event for a CRM event"""
        crm_type = crm_event.get("meeting_type", "")
        
        # Skip internal meetings for matching
        if crm_type == "Internal":
            return None
        
        crm_dt = self.get_crm_datetime(crm_event)
        crm_client = crm_event.get("client_company", "")
        
        best_match = None
        best_score = 0.0
        
        for cal_event in self.calendar_events:
            if cal_event["event_id"] in used_calendar_ids:
                continue
            
            cal_dt = self.get_calendar_datetime(cal_event)
            
            # Must have matching date
            if crm_dt and cal_dt:
                if not self.is_time_overlap(crm_dt, cal_dt, tolerance_hours=4):
                    continue
            else:
                continue
            
            # Skip internal events
            cal_title = cal_event.get("title", "").lower()
            if any(x in cal_title for x in ["weekly team", "internal", "prep", "board"]):
                if "client" not in cal_title:
                    continue
            
            # Calculate match score
            client_score = self.is_client_match(crm_event, cal_event)
            subject_score = self.is_subject_match(crm_event, cal_event)
            
            # Weighted score: client match is more important
            total_score = (client_score * 0.6) + (subject_score * 0.4)
            
            if total_score > best_score and total_score > 0.3:  # Threshold
                best_score = total_score
                best_match = cal_event
        
        return best_match
    
    def reconcile(self) -> Dict:
        """Run reconciliation and return results"""
        used_calendar_ids = set()
        reconciled_meetings = []
        
        # Process CRM events
        for crm_event in self.crm_events:
            crm_type = crm_event.get("meeting_type", "")
            
            # Store internal events separately
            if crm_type == "Internal":
                self.internal_events.append(crm_event)
                continue
            
            # Try to find matching calendar event
            matched_cal = self.try_match_event(crm_event, used_calendar_ids)
            
            if matched_cal:
                used_calendar_ids.add(matched_cal["event_id"])
                self.matched_pairs.append((crm_event, matched_cal))
                reconciled_meetings.append({
                    "reconciliation_id": f"REC-{crm_event['crm_id']}-{matched_cal['event_id']}",
                    "source_crm_id": crm_event["crm_id"],
                    "source_calendar_id": matched_cal["event_id"],
                    "combined_data": self._combine_event_data(crm_event, matched_cal),
                    "data_conflicts": self._identify_conflicts(crm_event, matched_cal),
                    "confidence_score": 0.85,  # Would calculate based on match quality
                    "reconciliation_type": "Matched"
                })
            else:
                self.unmatched_crm.append(crm_event)
                reconciled_meetings.append({
                    "reconciliation_id": f"REC-{crm_event['crm_id']}-UNMATCHED",
                    "source_crm_id": crm_event["crm_id"],
                    "source_calendar_id": None,
                    "combined_data": self._crm_only_data(crm_event),
                    "data_conflicts": [],
                    "confidence_score": 0.0,
                    "reconciliation_type": "CRM Only"
                })
        
        # Process unmatched calendar events
        for cal_event in self.calendar_events:
            if cal_event["event_id"] not in used_calendar_ids:
                self.unmatched_calendar.append(cal_event)
                reconciled_meetings.append({
                    "reconciliation_id": f"REC-UNMATCHED-{cal_event['event_id']}",
                    "source_crm_id": None,
                    "source_calendar_id": cal_event["event_id"],
                    "combined_data": self._calendar_only_data(cal_event),
                    "data_conflicts": [],
                    "confidence_score": 0.0,
                    "reconciliation_type": "Calendar Only"
                })
        
        return {
            "total_reconciled": len(reconciled_meetings),
            "matched_pairs": len(self.matched_pairs),
            "unmatched_crm": len(self.unmatched_crm),
            "unmatched_calendar": len(self.unmatched_calendar),
            "internal_events": len(self.internal_events),
            "meetings": reconciled_meetings
        }
    
    def _combine_event_data(self, crm_event: Dict, cal_event: Dict) -> Dict:
        """Combine data from both sources"""
        return {
            "meeting_type": crm_event.get("meeting_type", cal_event.get("event_type", "Unknown")),
            "subject": crm_event.get("subject", cal_event.get("title", "")),
            "client_name": crm_event.get("client_name"),
            "client_company": crm_event.get("client_company"),
            "relationship_owner": crm_event.get("relationship_owner"),
            "meeting_date": self.normalize_date(crm_event.get("meeting_date")),
            "meeting_time": crm_event.get("meeting_time") or self._extract_time_from_cal(cal_event),
            "start_time": cal_event.get("start_time"),
            "end_time": cal_event.get("end_time"),
            "location_crm": crm_event.get("location"),
            "location_calendar": cal_event.get("location"),
            "location": crm_event.get("location") or cal_event.get("location"),
            "description": cal_event.get("description") or crm_event.get("notes", ""),
            "notes": crm_event.get("notes"),
            "attendees": cal_event.get("attendees", []),
            "organizer": cal_event.get("organizer"),
            "status": crm_event.get("status", cal_event.get("status")),
            "crm_status": crm_event.get("status"),
            "calendar_status": cal_event.get("status")
        }
    
    def _crm_only_data(self, crm_event: Dict) -> Dict:
        """Format CRM-only event"""
        return {
            "meeting_type": crm_event.get("meeting_type", "Unknown"),
            "subject": crm_event.get("subject", ""),
            "client_name": crm_event.get("client_name"),
            "client_company": crm_event.get("client_company"),
            "relationship_owner": crm_event.get("relationship_owner"),
            "meeting_date": self.normalize_date(crm_event.get("meeting_date")),
            "meeting_time": crm_event.get("meeting_time"),
            "location": crm_event.get("location"),
            "description": crm_event.get("notes"),
            "status": crm_event.get("status"),
            "source": "CRM"
        }
    
    def _calendar_only_data(self, cal_event: Dict) -> Dict:
        """Format calendar-only event"""
        return {
            "meeting_type": "Unknown",
            "subject": cal_event.get("title", ""),
            "start_time": cal_event.get("start_time"),
            "end_time": cal_event.get("end_time"),
            "location": cal_event.get("location"),
            "description": cal_event.get("description"),
            "attendees": cal_event.get("attendees", []),
            "organizer": cal_event.get("organizer"),
            "status": cal_event.get("status"),
            "source": "Calendar"
        }
    
    def _extract_time_from_cal(self, cal_event: Dict) -> Optional[str]:
        """Extract time from calendar start_time"""
        try:
            start_time = cal_event.get("start_time")
            if start_time:
                if 'T' in start_time:
                    return start_time.split('T')[1][:5]
        except Exception:
            pass
        return None
    
    def _identify_conflicts(self, crm_event: Dict, cal_event: Dict) -> List[Dict]:
        """Identify conflicts between CRM and calendar data"""
        conflicts = []
        
        # Time conflict
        crm_time = crm_event.get("meeting_time")
        cal_start = cal_event.get("start_time")
        if crm_time and cal_start:
            cal_time = self._extract_time_from_cal(cal_event)
            if crm_time != cal_time:
                conflicts.append({
                    "field": "meeting_time",
                    "crm_value": crm_time,
                    "calendar_value": cal_time,
                    "severity": "low"
                })
        
        # Location conflict
        crm_loc = crm_event.get("location")
        cal_loc = cal_event.get("location")
        if crm_loc and cal_loc and crm_loc.lower() != cal_loc.lower():
            # Check if they're similar
            if self.similarity_score(crm_loc, cal_loc) < 0.7:
                conflicts.append({
                    "field": "location",
                    "crm_value": crm_loc,
                    "calendar_value": cal_loc,
                    "severity": "medium"
                })
        
        # Status conflict
        crm_status = crm_event.get("status")
        cal_status = cal_event.get("status")
        if crm_status and cal_status and crm_status.lower() != cal_status.lower():
            conflicts.append({
                "field": "status",
                "crm_value": crm_status,
                "calendar_value": cal_status,
                "severity": "high"
            })
        
        return conflicts
