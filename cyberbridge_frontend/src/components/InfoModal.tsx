import React from 'react';
import { Modal } from 'antd';

interface InfoModalProps {
    visible: boolean;
    onClose: () => void;
    title: string;
    content: React.ReactNode;
}

const InfoModal: React.FC<InfoModalProps> = ({ visible, onClose, title, content }) => {
    return (
        <Modal
            title={<span style={{ color: '#0f386a', fontSize: '18px', fontWeight: 'bold' }}>{title}</span>}
            open={visible}
            onCancel={onClose}
            footer={null}
            width={700}
            centered
        >
            <div style={{ 
                fontSize: '14px', 
                lineHeight: '1.6', 
                color: '#333',
                padding: '10px 0'
            }}>
                {content}
            </div>
        </Modal>
    );
};

export default InfoModal;