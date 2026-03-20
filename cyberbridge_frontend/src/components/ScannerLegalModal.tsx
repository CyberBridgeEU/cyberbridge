import { Modal } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';

interface ScannerLegalModalProps {
    open: boolean;
    scannerName: string;
    onOk: () => void;
    onCancel: () => void;
}

const ScannerLegalModal = ({ open, scannerName, onOk, onCancel }: ScannerLegalModalProps) => (
    <Modal
        title={<span><ExclamationCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />Legal Disclaimer — {scannerName} Scan</span>}
        open={open}
        onOk={onOk}
        onCancel={onCancel}
        okText="I Accept — Proceed with Scan"
        cancelText="Cancel"
        width={600}
    >
        <p style={{ marginBottom: 12 }}>
            By proceeding with this scan, you acknowledge and agree to the following:
        </p>
        <ul style={{ paddingLeft: 20, marginBottom: 12 }}>
            <li style={{ marginBottom: 8 }}>
                <strong>Authorization: </strong>
                You confirm that you have written authorization from the owner of the target system(s) to perform this scan.
            </li>
            <li style={{ marginBottom: 8 }}>
                <strong>Legal Responsibility: </strong>
                You are solely responsible for ensuring that this scan complies with all applicable local, national, and international laws and regulations.
            </li>
            <li style={{ marginBottom: 8 }}>
                <strong>No Liability: </strong>
                CyberBridge and its developers accept no liability for any damage, disruption, data loss, or legal consequences arising from the use of this scanning tool.
            </li>
            <li style={{ marginBottom: 8 }}>
                <strong>Compliance: </strong>
                You agree to comply with all relevant legislation, including but not limited to the Computer Fraud and Abuse Act (CFAA), the General Data Protection Regulation (GDPR), and equivalent laws in your jurisdiction.
            </li>
        </ul>
        <p style={{ marginTop: 8, fontStyle: 'italic', color: '#888' }}>
            Unauthorized scanning of systems you do not own or have permission to test may be a criminal offense.
        </p>
    </Modal>
);

export default ScannerLegalModal;
