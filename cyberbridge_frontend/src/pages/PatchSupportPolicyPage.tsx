import { ToolOutlined } from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const sections = [
    {
        number: 1,
        title: 'Support Period Declaration',
        description: 'Clearly state the minimum support period for your product with digital elements. Under the CRA, this must be at least 5 years from the date the product is placed on the market, or the expected product lifetime — whichever is shorter.'
    },
    {
        number: 2,
        title: 'Update Delivery Timelines',
        description: 'Define the maximum timeframe for delivering security updates after a vulnerability is identified. Include timelines for critical patches (e.g., 24–72 hours), high-severity fixes, and routine updates.'
    },
    {
        number: 3,
        title: 'SLA Definitions',
        description: 'Establish service-level agreements for patch response times based on vulnerability severity. Document escalation procedures and communication channels for each SLA tier.'
    },
    {
        number: 4,
        title: 'End-of-Support Policy',
        description: 'Define the process for end-of-support notification, including minimum advance notice periods, migration guidance, and final security update commitments before support ends.'
    },
    {
        number: 5,
        title: 'Customer Notification Process',
        description: 'Describe how users will be informed about available security updates. This must include automatic notification mechanisms and clear instructions for applying patches.'
    },
    {
        number: 6,
        title: 'Emergency Patch Procedures',
        description: 'Document the expedited process for handling zero-day vulnerabilities and actively exploited flaws. Include out-of-band release criteria, rollback procedures, and emergency communication plans.'
    }
];

const PatchSupportPolicyPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    return (
        <div>
            <div className={'page-parent'}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <ToolOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Patch & Support Policy</h1>
                        </div>
                    </div>

                    {/* Intro */}
                    <div style={{
                        backgroundColor: '#fff',
                        borderRadius: '8px',
                        border: '1px solid #f0f0f0',
                        padding: '24px',
                        marginTop: '20px'
                    }}>
                        <p style={{ margin: 0, lineHeight: 1.7, color: '#444', fontSize: '14px' }}>
                            The <strong>Cyber Resilience Act (CRA)</strong> requires manufacturers to handle vulnerabilities
                            effectively for the entire support period of their products with digital elements. This includes
                            providing timely security updates free of charge, notifying users of available patches, and
                            maintaining a documented policy for ongoing security support. A robust patch and support policy
                            is essential to demonstrate compliance with CRA obligations.
                        </p>
                    </div>

                    {/* Section Cards */}
                    <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#333', margin: '28px 0 16px' }}>
                        Mandatory Elements
                    </h2>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                        gap: '16px'
                    }}>
                        {sections.map((section) => (
                            <div
                                key={section.number}
                                style={{
                                    backgroundColor: '#fff',
                                    borderRadius: '8px',
                                    border: '1px solid #f0f0f0',
                                    padding: '20px',
                                    display: 'flex',
                                    gap: '14px',
                                    transition: 'border-color 0.2s'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.borderColor = '#0f386a';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.borderColor = '#f0f0f0';
                                }}
                            >
                                <div style={{
                                    width: '32px',
                                    height: '32px',
                                    borderRadius: '50%',
                                    backgroundColor: '#f0f7ff',
                                    color: '#0f386a',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontWeight: 700,
                                    fontSize: '14px',
                                    flexShrink: 0
                                }}>
                                    {section.number}
                                </div>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '14px', color: '#333', marginBottom: '6px' }}>
                                        {section.title}
                                    </div>
                                    <div style={{ fontSize: '13px', color: '#666', lineHeight: 1.6 }}>
                                        {section.description}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Info Box */}
                    <div style={{
                        backgroundColor: '#f0f7ff',
                        borderRadius: '8px',
                        border: '1px solid #d6e8f7',
                        padding: '24px',
                        marginTop: '28px'
                    }}>
                        <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#1a3c6e', margin: '0 0 12px' }}>
                            CRA Article 13 — Security Update Obligations
                        </h3>
                        <ul style={{ margin: 0, paddingLeft: '20px', color: '#444', fontSize: '14px', lineHeight: 1.8 }}>
                            <li><strong>Free security updates</strong> — manufacturers must provide security patches free of charge for the entire support period, delivered without undue delay.</li>
                            <li><strong>Automatic update mechanisms</strong> — products must support automatic security updates with a user opt-out option, and updates must be separate from functionality updates where technically feasible.</li>
                            <li><strong>Vulnerability remediation</strong> — once a vulnerability is identified, the manufacturer must address it without delay by applying effective and proportionate security updates.</li>
                            <li><strong>User notification</strong> — manufacturers must inform users about vulnerabilities and available updates through effective channels, including on the product website.</li>
                        </ul>
                    </div>

                    <div style={{ marginBottom: '28px' }} />
                </div>
            </div>
        </div>
    );
};

export default PatchSupportPolicyPage;
