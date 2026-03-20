# Scanner History Implementation Guide

## Overview
This document describes the complete implementation of scanner history functionality for the CyberBridge platform, allowing users to persist, view, and manage their scan results across ZAP, Nmap, Semgrep, and OSV scanners.

## Completed Implementation

### 1. Backend Implementation ✅

#### Database Model
**File:** `cyberbridge_backend/app/models/models.py`

Added `ScannerHistory` table with the following schema:
- `id` (UUID, primary key)
- `scanner_type` (String - zap/nmap/semgrep/osv)
- `user_id` (UUID, foreign key to users)
- `user_email` (String)
- `organisation_id` (UUID, foreign key to organisations, nullable)
- `organisation_name` (String, nullable)
- `scan_target` (String - URL or filename)
- `scan_type` (String, nullable - e.g., spider/active/full for ZAP)
- `scan_config` (Text, nullable - JSON configuration)
- `results` (Text - JSON string of scan results)
- `summary` (Text, nullable - LLM analysis)
- `status` (String - completed/failed/in_progress)
- `error_message` (Text, nullable)
- `scan_duration` (Float, nullable - in seconds)
- `timestamp` (DateTime)
- `created_at` (DateTime)
- `updated_at` (DateTime)

#### DTOs/Schemas
**File:** `cyberbridge_backend/app/dtos/schemas.py`

Added three schema classes:
- `ScannerHistoryBase` - Base fields for scanner history
- `ScannerHistoryCreate` - For creating new records
- `ScannerHistoryResponse` - For API responses

#### Repository Layer
**File:** `cyberbridge_backend/app/repositories/scanner_history_repository.py`

Implemented functions:
- `create_scanner_history()` - Create new history record
- `get_scanner_history_by_id()` - Get single record by ID
- `get_all_scanner_history()` - Get all records with filtering
- `get_scanner_history_by_scanner_type()` - Get records by scanner type
- `get_scanner_history_count()` - Count records with filtering
- `delete_scanner_history()` - Delete a record
- `delete_old_scanner_history()` - Cleanup old records

#### API Endpoints
**File:** `cyberbridge_backend/app/routers/scanners_controller.py`

Added endpoints:
- `POST /scanners/history` - Create new history record
- `GET /scanners/history` - Get all history (filtered by org for non-super-admins)
- `GET /scanners/history/{scanner_type}` - Get history by scanner type
- `GET /scanners/history/details/{history_id}` - Get specific record details
- `DELETE /scanners/history/{history_id}` - Delete record (super admin only)

### 2. Frontend Implementation ✅

#### Utility Functions
**File:** `cyberbridge_frontend/src/utils/scannerHistoryUtils.ts`

Implemented functions:
- `fetchCurrentUserDetails()` - Get user and organization info
- `saveScannerHistory()` - Save scan results to history
- `fetchScannerHistory()` - Retrieve history records
- `parseHistoryResults()` - Parse JSON results safely
- `formatTimestamp()` - Format timestamps for display

#### Grid Column Definitions
**File:** `cyberbridge_frontend/src/constants/ScannerHistoryGridColumns.tsx`

Implemented:
- `ScannerHistoryGridColumns()` - Reusable column definitions
- `prepareHistoryTableData()` - Data preparation function
- Columns include: Timestamp, Target, Scan Type, Status, Duration, User, Organization

#### ZAP Page with Full History ✅
**File:** `cyberbridge_frontend/src/pages/ZapPage.tsx`

Fully implemented with:
1. **State Management:**
   - Scanner history list
   - History loading state
   - History modal visibility
   - Selected history record
   - Historical results for viewing

2. **Effects:**
   - Load history on page mount
   - Auto-save history when scan completes
   - Track scan duration
   - Monitor scan completion status

3. **UI Components:**
   - Tabs for "Current Scan" and "Scan History"
   - History table with all columns
   - "View Results" action button
   - Modal to display historical scan results with full ZAP alert table
   - Refresh button to reload history

4. **Features:**
   - Automatic history saving when scan completes
   - Duration tracking
   - Status badges (completed/failed/in_progress)
   - Historical results displayed in same format as current results
   - Full alert details in expandable rows

### 3. Pattern for Other Scanners

The same pattern should be applied to **Nmap**, **Semgrep**, and **OSV** pages with these modifications:

#### Key Changes for Each Scanner:

**Nmap Page** (`NmapPage.tsx`):
- Scanner type: `'nmap'`
- Results format: Store `scanResults` as text/JSON
- History modal should display results in a `<pre>` tag or formatted display

**Semgrep Page** (`SemgrepPage.tsx`):
- Scanner type: `'semgrep'`
- Results format: Store `scanResults` as text/JSON
- History modal should display formatted results

**OSV Page** (`OsvPage.tsx`):
- Scanner type: `'osv'`
- Results format: Store `scanResults` as text/JSON
- History modal should display formatted results

#### Implementation Steps for Remaining Pages:

1. **Add imports:**
```typescript
import { Tabs } from "antd";
import { HistoryOutlined } from '@ant-design/icons';
import { ScannerHistoryGridColumns, prepareHistoryTableData, ScannerHistoryRecord } from "../constants/ScannerHistoryGridColumns.tsx";
import {
    saveScannerHistory,
    fetchScannerHistory,
    fetchCurrentUserDetails
} from "../utils/scannerHistoryUtils.ts";

const { TabPane } = Tabs;
```

2. **Add state variables:**
```typescript
const [scannerHistory, setScannerHistory] = useState<ScannerHistoryRecord[]>([]);
const [historyLoading, setHistoryLoading] = useState(false);
const [historyModalVisible, setHistoryModalVisible] = useState(false);
const [selectedHistoryRecord, setSelectedHistoryRecord] = useState<ScannerHistoryRecord | null>(null);
const [historicalResults, setHistoricalResults] = useState<string>('');
const [scanStartTime, setScanStartTime] = useState<number | null>(null);
```

3. **Add useEffects:**
```typescript
// Load history on mount
useEffect(() => {
    loadScannerHistory();
}, []);

// Save history when scan completes
useEffect(() => {
    const saveHistoryOnCompletion = async () => {
        if (scanResults && !loading && user?.email && scanStartTime) {
            const duration = (Date.now() - scanStartTime) / 1000;
            const userDetails = await fetchCurrentUserDetails(user.email);

            if (userDetails) {
                await saveScannerHistory(
                    {
                        scanner_type: 'nmap', // or 'semgrep', 'osv'
                        scan_target: target,
                        scan_type: scanType,
                        results: scanResults,
                        status: 'completed',
                        scan_duration: duration
                    },
                    userDetails.email,
                    userDetails.id,
                    userDetails.organisation_id,
                    userDetails.organisation_name
                );
                loadScannerHistory();
            }
            setScanStartTime(null);
        }
    };
    saveHistoryOnCompletion();
}, [scanResults, loading, user, scanStartTime]);

// Track scan start
useEffect(() => {
    if (loading && !scanStartTime) {
        setScanStartTime(Date.now());
    }
}, [loading, scanStartTime]);
```

4. **Add history functions:**
```typescript
const loadScannerHistory = async () => {
    setHistoryLoading(true);
    try {
        const history = await fetchScannerHistory('nmap', 100); // or 'semgrep', 'osv'
        setScannerHistory(history);
    } catch (error) {
        console.error('Error loading scanner history:', error);
    } finally {
        setHistoryLoading(false);
    }
};

const handleViewHistoryResults = (record: ScannerHistoryRecord) => {
    const results = parseHistoryResults(record.results);
    if (results) {
        setHistoricalResults(typeof results === 'string' ? results : JSON.stringify(results, null, 2));
        setSelectedHistoryRecord(record);
        setHistoryModalVisible(true);
    }
};
```

5. **Wrap content in Tabs and add History tab:**
```typescript
<Tabs defaultActiveKey="1">
    <TabPane tab="Current Scan" key="1">
        {/* Existing scanner content */}
    </TabPane>

    <TabPane tab={<span><HistoryOutlined /> Scan History</span>} key="2">
        <div className="page-section">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 className="section-title" style={{ margin: 0 }}>Previous Scans</h3>
                <button className="add-button" onClick={loadScannerHistory} disabled={historyLoading}>
                    {historyLoading ? 'Loading...' : 'Refresh'}
                </button>
            </div>

            <Table
                columns={[
                    ...ScannerHistoryGridColumns(),
                    {
                        title: 'Actions',
                        key: 'actions',
                        width: 120,
                        render: (_: any, record: ScannerHistoryRecord) => (
                            <Button type="link" onClick={() => handleViewHistoryResults(record)}>
                                View Results
                            </Button>
                        )
                    }
                ]}
                dataSource={prepareHistoryTableData(scannerHistory)}
                loading={historyLoading}
                pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} records`
                }}
                scroll={{ x: 1200 }}
                style={{
                    border: '1px solid #f0f0f0',
                    borderRadius: '6px'
                }}
            />
        </div>
    </TabPane>
</Tabs>
```

6. **Add history modal:**
```typescript
<Modal
    title={selectedHistoryRecord ? `Scan Results - ${formatTimestamp(selectedHistoryRecord.timestamp)}` : 'Scan Results'}
    open={historyModalVisible}
    onCancel={() => {
        setHistoryModalVisible(false);
        setSelectedHistoryRecord(null);
        setHistoricalResults('');
    }}
    footer={[
        <Button key="close" onClick={() => {
            setHistoryModalVisible(false);
            setSelectedHistoryRecord(null);
            setHistoricalResults('');
        }}>
            Close
        </Button>
    ]}
    width={1000}
>
    {selectedHistoryRecord && (
        <div>
            <div style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                <p><strong>Target:</strong> {selectedHistoryRecord.scan_target}</p>
                <p><strong>Scan Type:</strong> {selectedHistoryRecord.scan_type || 'N/A'}</p>
                <p><strong>Status:</strong> <Tag color={selectedHistoryRecord.status === 'completed' ? 'green' : 'red'}>{selectedHistoryRecord.status.toUpperCase()}</Tag></p>
                {selectedHistoryRecord.scan_duration && (
                    <p><strong>Duration:</strong> {selectedHistoryRecord.scan_duration.toFixed(2)}s</p>
                )}
            </div>

            <div style={{
                backgroundColor: '#f5f5f5',
                padding: '16px',
                borderRadius: '6px',
                maxHeight: '500px',
                overflow: 'auto',
                fontFamily: 'monospace',
                fontSize: '13px',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
            }}>
                {historicalResults}
            </div>
        </div>
    )}
</Modal>
```

## Testing Checklist

### Backend Testing:
- [x] Scanner history table created in database
- [ ] POST endpoint creates history records
- [ ] GET endpoints return filtered history
- [ ] Organization filtering works correctly
- [ ] Super admin can see all records
- [ ] Regular users see only their org's records

### Frontend Testing (ZAP):
- [x] History loads on page mount
- [ ] Scan completion triggers history save
- [ ] History table displays all columns correctly
- [ ] "View Results" shows historical ZAP alerts
- [ ] Historical results display in same format as current results
- [ ] Duration tracking works
- [ ] Refresh button reloads history

### Frontend Testing (Other Scanners):
- [ ] Nmap history implementation
- [ ] Semgrep history implementation
- [ ] OSV history implementation
- [ ] All scanners follow same pattern
- [ ] Historical results display correctly for each scanner type

## Database Migration (if using Alembic)

If you're using Alembic for migrations, create a migration:

```bash
cd cyberbridge_backend
alembic revision --autogenerate -m "add_scanner_history_table"
alembic upgrade head
```

## Files Created/Modified

### Backend:
1. `cyberbridge_backend/app/models/models.py` - Added ScannerHistory model
2. `cyberbridge_backend/app/dtos/schemas.py` - Added scanner history schemas
3. `cyberbridge_backend/app/repositories/scanner_history_repository.py` - New file
4. `cyberbridge_backend/app/routers/scanners_controller.py` - Added history endpoints

### Frontend:
1. `cyberbridge_frontend/src/utils/scannerHistoryUtils.ts` - New file
2. `cyberbridge_frontend/src/constants/ScannerHistoryGridColumns.tsx` - New file
3. `cyberbridge_frontend/src/pages/ZapPage.tsx` - Fully updated with history
4. `cyberbridge_frontend/src/pages/ZapPage.tsx.backup` - Original backup
5. `cyberbridge_frontend/src/pages/NmapPage.tsx` - Pending update
6. `cyberbridge_frontend/src/pages/SemgrepPage.tsx` - Pending update
7. `cyberbridge_frontend/src/pages/OsvPage.tsx` - Pending update

## Key Features

1. **Automatic History Saving**: Scans are automatically saved to history when completed
2. **Duration Tracking**: Scan duration is calculated and stored
3. **Organization Filtering**: Users see only their organization's scans (except super admins)
4. **Historical Results Viewing**: Full scan results can be viewed from history
5. **Status Tracking**: Scans tracked as completed/failed/in_progress
6. **User Attribution**: Each scan linked to user and organization
7. **Persistent Storage**: All results stored in database as JSON

## Next Steps

1. Apply the same pattern to Nmap, Semgrep, and OSV pages
2. Test all scanner history functionality
3. Add any custom formatting for historical results display per scanner type
4. Consider adding export functionality for historical scans
5. Consider adding delete functionality for users to manage their own history
6. Add analytics/reporting on scan history

## Notes

- ZAP results are stored as a JSON array of alerts
- Other scanner results are stored as text/JSON strings
- All timestamps are in UTC
- History is organization-scoped for security
- Super admins can see all organization's scans
- The backup of the original ZAP page is at `ZapPage.tsx.backup`
