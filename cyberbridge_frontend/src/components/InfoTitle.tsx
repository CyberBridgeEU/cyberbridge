import React, { useState } from 'react';
import { InfoCircleOutlined } from '@ant-design/icons';
import InfoModal from './InfoModal';

interface InfoTitleProps {
    title: string;
    infoContent: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
    icon?: React.ReactNode;
}

const InfoTitle: React.FC<InfoTitleProps> = ({ title, infoContent, className = 'page-title', style, icon }) => {
    const [isModalVisible, setIsModalVisible] = useState(false);

    const showModal = () => {
        setIsModalVisible(true);
    };

    const hideModal = () => {
        setIsModalVisible(false);
    };

    return (
        <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', ...style }}>
                {icon && <span style={{ fontSize: 28 }}>{icon}</span>}
                <h3 className={className} style={{ margin: 0 }}>
                    {title}
                </h3>
                <InfoCircleOutlined
                    onClick={showModal}
                    style={{
                        background: 'linear-gradient(135deg, #1a365d, #0f386a, #3D7ABD)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        fontSize: '16px',
                        cursor: 'pointer',
                        transition: 'opacity 0.2s ease',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
                    onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
                />
            </div>
            <InfoModal
                visible={isModalVisible}
                onClose={hideModal}
                title={`${title} - How to Use`}
                content={infoContent}
            />
        </>
    );
};

export default InfoTitle;