"""
Event Sync Service - FastAPI Backend
Provides REST API for reconciled meetings data
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os
from pathlib import Path
from reconciler import EventReconciler
from typing import List, Dict, Optional


app = FastAPI(
    title="Event Sync Service",
    description="Reconciles meetings from CRM and Calendar sources",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cache for reconciled data
reconciled_data = None
crm_events_data = None
calendar_events_data = None


def load_data():
    """Load data from JSON files"""
    global reconciled_data, crm_events_data, calendar_events_data
    
    base_path = Path(__file__).parent
    
    # Load CRM events
    crm_file = base_path / "data" / "crm_events.json"
    with open(crm_file, 'r') as f:
        crm_events_data = json.load(f)
    
    # Load Calendar events
    calendar_file = base_path / "data" / "calendar_events.json"
    with open(calendar_file, 'r') as f:
        calendar_events_data = json.load(f)
    
    # Perform reconciliation
    reconciler = EventReconciler(crm_events_data, calendar_events_data)
    reconciled_data = reconciler.reconcile()


@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    load_data()


@app.get("/")
async def root():
    """Root endpoint - serves index.html"""
    try:
        return FileResponse("static/index.html")
    except:
        return {
            "message": "Event Sync Service - API endpoints available at /docs",
            "endpoints": {
                "get_meetings": "/api/meetings",
                "get_meeting": "/api/meetings/{id}",
                "get_summary": "/api/summary",
                "get_conflicts": "/api/conflicts"
            }
        }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Event Sync Service"}


@app.get("/api/summary")
async def get_summary():
    """Get reconciliation summary"""
    if not reconciled_data:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    return {
        "total_meetings": reconciled_data["total_reconciled"],
        "matched_pairs": reconciled_data["matched_pairs"],
        "crm_only": reconciled_data["unmatched_crm"],
        "calendar_only": reconciled_data["unmatched_calendar"],
        "internal_meetings": reconciled_data["internal_events"],
        "data_quality": {
            "matched_percentage": round(
                (reconciled_data["matched_pairs"] / max(reconciled_data["total_reconciled"], 1)) * 100, 2
            )
        }
    }


@app.get("/api/meetings")
async def get_meetings(
    reconciliation_type: Optional[str] = None,
    has_conflicts: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get reconciled meetings with optional filtering"""
    if not reconciled_data:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    meetings = reconciled_data["meetings"]
    
    # Filter by reconciliation type
    if reconciliation_type:
        meetings = [m for m in meetings if m["reconciliation_type"] == reconciliation_type]
    
    # Filter by conflicts
    if has_conflicts is not None:
        if has_conflicts:
            meetings = [m for m in meetings if len(m.get("data_conflicts", [])) > 0]
        else:
            meetings = [m for m in meetings if len(m.get("data_conflicts", [])) == 0]
    
    # Pagination
    total = len(meetings)
    meetings = meetings[skip:skip + limit]
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(meetings),
        "meetings": meetings
    }


@app.get("/api/meetings/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Get a specific meeting by reconciliation ID"""
    if not reconciled_data:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    for meeting in reconciled_data["meetings"]:
        if meeting["reconciliation_id"] == meeting_id:
            return meeting
    
    raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")


@app.get("/api/conflicts")
async def get_conflicts(skip: int = 0, limit: int = 50):
    """Get all meetings with data conflicts"""
    if not reconciled_data:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    conflicts_list = [
        m for m in reconciled_data["meetings"]
        if len(m.get("data_conflicts", [])) > 0
    ]
    
    total = len(conflicts_list)
    conflicts_list = conflicts_list[skip:skip + limit]
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(conflicts_list),
        "conflicts": conflicts_list
    }


@app.get("/api/crm-events")
async def get_crm_events():
    """Get raw CRM events"""
    if not crm_events_data:
        raise HTTPException(status_code=500, detail="Data not loaded")
    return {"count": len(crm_events_data), "events": crm_events_data}


@app.get("/api/calendar-events")
async def get_calendar_events():
    """Get raw calendar events"""
    if not calendar_events_data:
        raise HTTPException(status_code=500, detail="Data not loaded")
    return {"count": len(calendar_events_data), "events": calendar_events_data}


@app.get("/api/statistics")
async def get_statistics():
    """Get detailed statistics about reconciliation"""
    if not reconciled_data:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    meetings = reconciled_data["meetings"]
    
    # Calculate statistics
    reconciliation_types = {}
    conflict_severity = {}
    total_conflicts = 0
    
    for meeting in meetings:
        rec_type = meeting["reconciliation_type"]
        reconciliation_types[rec_type] = reconciliation_types.get(rec_type, 0) + 1
        
        conflicts = meeting.get("data_conflicts", [])
        total_conflicts += len(conflicts)
        
        for conflict in conflicts:
            severity = conflict.get("severity", "unknown")
            conflict_severity[severity] = conflict_severity.get(severity, 0) + 1
    
    return {
        "total_meetings": len(meetings),
        "by_reconciliation_type": reconciliation_types,
        "total_conflicts": total_conflicts,
        "conflict_by_severity": conflict_severity,
        "average_conflicts_per_meeting": round(total_conflicts / max(len(meetings), 1), 2)
    }


@app.get("/api/meetings-by-client")
async def get_meetings_by_client():
    """Get meetings grouped by client"""
    if not reconciled_data:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    by_client = {}
    
    for meeting in reconciled_data["meetings"]:
        combined = meeting.get("combined_data", {})
        client = combined.get("client_company") or combined.get("client_name") or "Unknown"
        
        if client not in by_client:
            by_client[client] = []
        by_client[client].append(meeting)
    
    return {"clients": by_client}


@app.get("/api/meetings-by-date")
async def get_meetings_by_date():
    """Get meetings grouped by date"""
    if not reconciled_data:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    by_date = {}
    
    for meeting in reconciled_data["meetings"]:
        combined = meeting.get("combined_data", {})
        date = combined.get("meeting_date") or combined.get("start_time", "Unknown")
        
        if isinstance(date, str) and "T" in date:
            date = date.split("T")[0]
        
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(meeting)
    
    # Sort by date
    sorted_dates = {}
    for date in sorted(by_date.keys()):
        sorted_dates[date] = by_date[date]
    
    return {"meetings_by_date": sorted_dates}


# Mount static files (frontend)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
