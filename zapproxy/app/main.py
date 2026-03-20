from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import requests

# ZAP Proxy Configuration
ZAP_HOST = "http://127.0.0.1"
ZAP_PORT = "8080"
ZAP_BASE = f"{ZAP_HOST}:{ZAP_PORT}"

app = FastAPI()

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporary: allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

def cleanup_and_reset():
    """Stop all scans, clear all data, and start a new session"""
    cleanup_results = {
        "actions_taken": [],
        "errors": []
    }

    try:
        # Stop all active scans
        stop_all_url = f"{ZAP_BASE}/JSON/ascan/action/stopAllScans/"
        requests.get(stop_all_url)
        cleanup_results["actions_taken"].append("Stopped all active scans")

        # Stop all spider scans
        spider_scans_url = f"{ZAP_BASE}/JSON/spider/view/scans/"
        spider_scans_response = requests.get(spider_scans_url).json()

        for scan in spider_scans_response.get("scans", []):
            scan_id = scan.get("id")
            if scan_id:
                stop_url = f"{ZAP_BASE}/JSON/spider/action/stop/?scanId={scan_id}"
                requests.get(stop_url)

        cleanup_results["actions_taken"].append("Stopped all spider scans")

        # Clear all alerts
        clear_alerts_url = f"{ZAP_BASE}/JSON/core/action/deleteAllAlerts/"
        requests.get(clear_alerts_url)
        cleanup_results["actions_taken"].append("Cleared all alerts")

        # Start new session (clears all discovered URLs and scan data)
        new_session_url = f"{ZAP_BASE}/JSON/core/action/newSession/"
        requests.get(new_session_url)
        cleanup_results["actions_taken"].append("Started new session")

        # Small delay to ensure cleanup is complete
        time.sleep(1)

    except Exception as e:
        cleanup_results["errors"].append(f"Cleanup failed: {str(e)}")

    return cleanup_results

@app.get("/")
async def root():
    return {"message": "zap proxy rest api is up and running!"}

@app.get("/start-spider/")
def start_spider(target_url: str):
    """ Start the Spider Scan (Crawls the website to discover links) """
    # Clean up and reset before starting new scan
    cleanup_results = cleanup_and_reset()

    spider_url = f"{ZAP_BASE}/JSON/spider/action/scan/?url={target_url}"
    response = requests.get(spider_url)

    result = response.json()
    result["cleanup_results"] = cleanup_results
    return result

@app.get("/start-active-scan/")
def start_active_scan(target_url: str):
    """ Start the Active Scan (Actively attacks and tests vulnerabilities) """
    # Clean up and reset before starting new scan
    cleanup_results = cleanup_and_reset()

    active_scan_url = f"{ZAP_BASE}/JSON/ascan/action/scan/?url={target_url}"
    response = requests.get(active_scan_url)

    result = response.json()
    result["cleanup_results"] = cleanup_results
    return result

# @app.get("/start-full-scan/")
# def start_full_scan(target_url: str):
#     """ Start Full Scan (Runs both Spider and Active Scan) """
#     spider_url = f"{ZAP_BASE}/JSON/spider/action/scan/?url={target_url}"
#     requests.get(spider_url)
#     time.sleep(5)  # Allow some time for crawling
#
#     active_scan_url = f"{ZAP_BASE}/JSON/ascan/action/scan/?url={target_url}"
#     response = requests.get(active_scan_url)
#     return {"message": "Full scan started", "target": target_url, "scan_info": response.json()}

@app.get("/start-full-scan/")
def start_full_scan(target_url: str):
    """Start Full Scan (Runs both Spider and Active Scan) with proper verification"""
    # Clean up and reset before starting new scan
    cleanup_results = cleanup_and_reset()

    # Start spider scan
    spider_url = f"{ZAP_BASE}/JSON/spider/action/scan/?url={target_url}"
    spider_response = requests.get(spider_url)
    spider_id = spider_response.json().get('scan')

    # Wait for spider to complete
    while True:
        spider_status = requests.get(f"{ZAP_BASE}/JSON/spider/view/status/?scanId={spider_id}").json()
        if spider_status.get('status') == '100':
            break
        time.sleep(2)

    # Ensure spider found URLs before starting active scan
    urls_url = f"{ZAP_BASE}/JSON/core/view/urls/"
    urls_response = requests.get(urls_url).json()
    discovered_urls = urls_response.get('urls', [])

    # Start active scan with verification
    active_scan_url = f"{ZAP_BASE}/JSON/ascan/action/scan/?url={target_url}&recurse=true&inScopeOnly=&scanPolicyName=&method=&postData=&contextId="
    active_response = requests.get(active_scan_url)
    scan_id = active_response.json().get('scan')

    # Verify active scan started
    verify_url = f"{ZAP_BASE}/JSON/ascan/view/status/?scanId={scan_id}"
    verify_response = requests.get(verify_url).json()

    return {
        "message": "Full scan started",
        "target": target_url,
        "cleanup_results": cleanup_results,
        "spider_results": {
            "id": spider_id,
            "urls_discovered": len(discovered_urls),
            "discovered_urls": discovered_urls
        },
        "active_scan": {
            "id": scan_id,
            "initial_status": verify_response,
        },
        "monitoring_endpoints": {
            "spider_status": f"/get-spider-status/?scan_id={spider_id}",
            "scan_status": f"/get-scan-status/?scan_id={scan_id}",
            "scan_progress": "/check-active-scan-state/",
            "results": f"/get-alerts/?target_url={target_url}"
        }
    }

@app.get("/check-active-scan-state/")
def check_active_scan_state(scan_id: int = None):
    """Check if active scan is running and get detailed status"""
    
    if scan_id:
        # Get specific scan progress
        running_status_url = f"{ZAP_BASE}/JSON/ascan/view/scanProgress/?scanId={scan_id}"
        running_response = requests.get(running_status_url)
        scan_progress = running_response.json()
    else:
        # Get all scans progress
        scan_progress = {"message": "No specific scan ID provided"}
    
    # Get all active scans
    scans_url = f"{ZAP_BASE}/JSON/ascan/view/scans/"
    scans_response = requests.get(scans_url)
    
    return {
        "scanner_progress": scan_progress,
        "active_scans": scans_response.json()
    }

@app.get("/get-comprehensive-scan-results/")
def get_comprehensive_scan_results(scan_id: int, target_url: str):
    """Get detailed scan results including scan status and categorized alerts"""
    # Get scan status
    scan_status_url = f"{ZAP_BASE}/JSON/ascan/view/status/?scanId={scan_id}"
    status_response = requests.get(scan_status_url).json()

    # Get scan progress details
    progress_url = f"{ZAP_BASE}/JSON/ascan/view/scanProgress/?scanId={scan_id}"
    progress_response = requests.get(progress_url).json()

    # Get alerts
    alerts_url = f"{ZAP_BASE}/JSON/core/view/alerts/"
    alerts_response = requests.get(alerts_url).json()

    # Filter and categorize alerts
    alerts = alerts_response.get("alerts", [])
    target_alerts = [alert for alert in alerts if target_url in alert.get("url", "")]

    # Categorize alerts by source (if possible)
    categorized_alerts = {
        "passive_scan_alerts": [],
        "active_scan_alerts": [],
        "uncategorized": []
    }

    for alert in target_alerts:
        # ZAP typically includes source information in alerts
        source = alert.get("source", "unknown")
        if "Active" in source:
            categorized_alerts["active_scan_alerts"].append(alert)
        elif "Passive" in source:
            categorized_alerts["passive_scan_alerts"].append(alert)
        else:
            categorized_alerts["uncategorized"].append(alert)

    return {
        "scan_status": {
            "completion": status_response.get('status'),
            "state": "Complete" if status_response.get('status') == '100' else "In Progress",
            "detailed_progress": progress_response
        },
        "alerts_summary": {
            "total_alerts": len(target_alerts),
            "active_scan_alerts": len(categorized_alerts["active_scan_alerts"]),
            "passive_scan_alerts": len(categorized_alerts["passive_scan_alerts"]),
            "uncategorized": len(categorized_alerts["uncategorized"])
        },
        "detailed_alerts": categorized_alerts
    }

@app.post("/run-passive-scan/")
def run_passive_scan(target_url: str):
    """ Run passive scan on discovered URLs """
    # ZAP automatically runs passive scans on spidered URLs
    # This endpoint just triggers alerts collection
    alerts_url = f"{ZAP_BASE}/JSON/core/view/alerts/"
    response = requests.get(alerts_url).json()

    # Filter alerts for the specific target URL
    filtered_alerts = [
        alert for alert in response.get("alerts", [])
        if target_url in alert.get("url", "")
    ]

    return {
        "message": "Passive scan results retrieved",
        "target_url": target_url,
        "alerts": filtered_alerts,
        "total_alerts": len(filtered_alerts)
    }

@app.get("/start-api-scan/")
def start_api_scan(api_url: str):
    """ Start API Scan (Scans API endpoints using OpenAPI/Swagger definition) """
    api_scan_url = f"{ZAP_BASE}/JSON/openapi/action/importUrl/?url={api_url}"
    response = requests.get(api_scan_url)
    return response.json()

# @app.get("/get-alerts/")
# def get_alerts():
#     """ Fetch all security alerts and return JSON results """
#     alerts_url = f"{ZAP_BASE}/JSON/core/view/alerts/"
#     response = requests.get(alerts_url)
#     return response.json()

@app.get("/get-alerts/")
def get_alerts(target_url: str = None):
    """ Fetch all security alerts, optionally filter by target URL """
    alerts_url = f"{ZAP_BASE}/JSON/core/view/alerts/"
    response = requests.get(alerts_url).json()

    if target_url:
        # Filter alerts for the specific target URL
        filtered_alerts = [
            alert for alert in response.get("alerts", []) if target_url in alert.get("url", "")
        ]
        return {"alerts": filtered_alerts}

    return response

@app.get("/clear-alerts/")
def clear_alerts():
    """ Clear all existing alerts before running a new scan """
    clear_url = f"{ZAP_BASE}/JSON/core/action/deleteAllAlerts/"
    response = requests.get(clear_url)
    return {"message": "All alerts cleared", "response": response.json()}

@app.get("/get-scan-status/")
def get_scan_status(scan_id: int):
    """ Check the status of an ongoing scan """
    scan_status_url = f"{ZAP_BASE}/JSON/ascan/view/status/?scanId={scan_id}"
    response = requests.get(scan_status_url)
    return response.json()

@app.get("/get-spider-status/")
def get_spider_status(scan_id: int):
    """ Check the status of an ongoing spider scan """
    spider_status_url = f"{ZAP_BASE}/JSON/spider/view/status/?scanId={scan_id}"
    response = requests.get(spider_status_url)
    return response.json()

@app.get("/get-scanned-urls/")
def get_scanned_urls():
    """ Retrieve all URLs scanned by ZAP """
    urls_url = f"{ZAP_BASE}/JSON/core/view/urls/"
    response = requests.get(urls_url)
    return response.json()

# ********************** enhance the API with more detailed endpoints **************************

# ==================== SCAN CONTROL ENDPOINTS ====================

@app.post("/stop-active-scan/")
def stop_active_scan(scan_id: int):
    """Stop a specific active scan by scan ID"""
    stop_url = f"{ZAP_BASE}/JSON/ascan/action/stop/?scanId={scan_id}"
    response = requests.get(stop_url)
    
    # Verify the scan was stopped
    status_url = f"{ZAP_BASE}/JSON/ascan/view/status/?scanId={scan_id}"
    status_response = requests.get(status_url).json()
    
    return {
        "message": f"Stop command sent for scan {scan_id}",
        "stop_response": response.json(),
        "current_status": status_response,
        "scan_id": scan_id
    }

@app.post("/stop-spider-scan/")
def stop_spider_scan(scan_id: int):
    """Stop a specific spider scan by scan ID"""
    stop_url = f"{ZAP_BASE}/JSON/spider/action/stop/?scanId={scan_id}"
    response = requests.get(stop_url)
    
    # Verify the spider was stopped
    status_url = f"{ZAP_BASE}/JSON/spider/view/status/?scanId={scan_id}"
    status_response = requests.get(status_url).json()
    
    return {
        "message": f"Stop command sent for spider scan {scan_id}",
        "stop_response": response.json(),
        "current_status": status_response,
        "scan_id": scan_id
    }

@app.post("/stop-all-scans/")
def stop_all_scans():
    """Stop ALL active scans (both spider and active scans)"""
    results = {
        "active_scans_stopped": [],
        "spider_scans_stopped": [],
        "errors": []
    }
    
    try:
        # Get all active scans and stop them
        active_scans_url = f"{ZAP_BASE}/JSON/ascan/view/scans/"
        active_scans_response = requests.get(active_scans_url).json()
        
        for scan in active_scans_response.get("scans", []):
            scan_id = scan.get("id")
            if scan_id:
                try:
                    stop_url = f"{ZAP_BASE}/JSON/ascan/action/stop/?scanId={scan_id}"
                    stop_response = requests.get(stop_url)
                    results["active_scans_stopped"].append({
                        "scan_id": scan_id,
                        "response": stop_response.json()
                    })
                except Exception as e:
                    results["errors"].append(f"Failed to stop active scan {scan_id}: {str(e)}")
    
    except Exception as e:
        results["errors"].append(f"Failed to get active scans: {str(e)}")
    
    try:
        # Get all spider scans and stop them
        spider_scans_url = f"{ZAP_BASE}/JSON/spider/view/scans/"
        spider_scans_response = requests.get(spider_scans_url).json()
        
        for scan in spider_scans_response.get("scans", []):
            scan_id = scan.get("id")
            if scan_id:
                try:
                    stop_url = f"{ZAP_BASE}/JSON/spider/action/stop/?scanId={scan_id}"
                    stop_response = requests.get(stop_url)
                    results["spider_scans_stopped"].append({
                        "scan_id": scan_id,
                        "response": stop_response.json()
                    })
                except Exception as e:
                    results["errors"].append(f"Failed to stop spider scan {scan_id}: {str(e)}")
    
    except Exception as e:
        results["errors"].append(f"Failed to get spider scans: {str(e)}")
    
    # Stop all active scans with the global stop command
    try:
        global_stop_url = f"{ZAP_BASE}/JSON/ascan/action/stopAllScans/"
        global_stop_response = requests.get(global_stop_url)
        results["global_stop_response"] = global_stop_response.json()
    except Exception as e:
        results["errors"].append(f"Failed to execute global stop: {str(e)}")
    
    return {
        "message": "Stop commands sent for all scans",
        "results": results,
        "timestamp": time.time()
    }

@app.get("/list-all-scans/")
def list_all_scans():
    """List all current scans (both active and spider) with their status"""
    try:
        # Get active scans
        active_scans_url = f"{ZAP_BASE}/JSON/ascan/view/scans/"
        active_scans_response = requests.get(active_scans_url).json()
        
        # Get spider scans
        spider_scans_url = f"{ZAP_BASE}/JSON/spider/view/scans/"
        spider_scans_response = requests.get(spider_scans_url).json()
        
        # Get scan progress for each active scan individually
        scan_progress_details = []
        for scan in active_scans_response.get("scans", []):
            scan_id = scan.get("id")
            if scan_id:
                try:
                    progress_url = f"{ZAP_BASE}/JSON/ascan/view/scanProgress/?scanId={scan_id}"
                    progress_response = requests.get(progress_url).json()
                    scan_progress_details.append({
                        "scan_id": scan_id,
                        "progress": progress_response
                    })
                except Exception as e:
                    # Handle case where scan doesn't exist or other errors
                    scan_progress_details.append({
                        "scan_id": scan_id,
                        "error": f"Could not get progress: {str(e)}"
                    })
        
        return {
            "active_scans": active_scans_response.get("scans", []),
            "spider_scans": spider_scans_response.get("scans", []),
            "scan_progress_details": scan_progress_details,
            "total_active_scans": len(active_scans_response.get("scans", [])),
            "total_spider_scans": len(spider_scans_response.get("scans", []))
        }
        
    except Exception as e:
        return {
            "error": f"Failed to list scans: {str(e)}",
            "active_scans": [],
            "spider_scans": [],
            "scan_progress_details": []
        }

@app.post("/emergency-stop/")
def emergency_stop():
    """Emergency stop - forcefully stop everything and clear all data"""
    results = {
        "actions_taken": [],
        "errors": []
    }
    
    try:
        # Stop all scans
        stop_result = stop_all_scans()
        results["actions_taken"].append("Attempted to stop all scans")
        results["stop_all_result"] = stop_result
        
        # Clear all alerts
        clear_alerts_url = f"{ZAP_BASE}/JSON/core/action/deleteAllAlerts/"
        clear_response = requests.get(clear_alerts_url)
        results["actions_taken"].append("Cleared all alerts")
        results["clear_alerts_response"] = clear_response.json()
        
        # Clear session (this removes all discovered URLs and scan data)
        new_session_url = f"{ZAP_BASE}/JSON/core/action/newSession/"
        session_response = requests.get(new_session_url)
        results["actions_taken"].append("Created new session (cleared all data)")
        results["new_session_response"] = session_response.json()
        
        return {
            "message": "Emergency stop completed - all scans stopped and data cleared",
            "results": results,
            "timestamp": time.time()
        }
        
    except Exception as e:
        results["errors"].append(f"Emergency stop failed: {str(e)}")
        return {
            "message": "Emergency stop encountered errors",
            "results": results,
            "timestamp": time.time()
        }
