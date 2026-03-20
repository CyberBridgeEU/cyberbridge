import { ProfileOutlined } from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const sections = [
    {
        number: 1,
        title: 'Format Requirements (SPDX / CycloneDX)',
        description: 'Generate SBOMs in a machine-readable, industry-standard format — SPDX or CycloneDX. The chosen format must support all required metadata fields and be interoperable with common tooling.'
    },
    {
        number: 2,
        title: 'Top-Level Dependency Listing',
        description: 'At minimum, document all top-level dependencies of the product. The CRA specifically requires identification of components and their versions included in the product with digital elements.'
    },
    {
        number: 3,
        title: 'Generation Frequency',
        description: 'Define the cadence for SBOM regeneration — at minimum upon each release, but ideally as part of every CI/CD build. Document triggers for ad-hoc regeneration such as dependency updates or vulnerability disclosures.'
    },
    {
        number: 4,
        title: 'Version Tracking',
        description: 'Each SBOM must be versioned and linked to the specific product release it describes. Maintain an archive of historical SBOMs to support auditability and traceability over the product lifecycle.'
    },
    {
        number: 5,
        title: 'Machine-Readable Delivery',
        description: 'SBOMs must be made available in a machine-readable format to downstream users, market surveillance authorities, and — upon request — to ENISA. Consider automated delivery mechanisms such as API endpoints or package registry metadata.'
    },
    {
        number: 6,
        title: 'SBOM Update Policy',
        description: 'Establish a policy for updating SBOMs when dependencies change, vulnerabilities are discovered, or components are replaced. Define responsibilities, review processes, and maximum update latency from change to publication.'
    }
];

const SbomManagementPage = () => {
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
                            <ProfileOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>SBOM Management</h1>
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
                            The <strong>Cyber Resilience Act (CRA)</strong> requires manufacturers to identify and document
                            the components contained in their products with digital elements, including through a
                            Software Bill of Materials (SBOM). The SBOM must cover at minimum the top-level dependencies
                            and be generated in a commonly used, machine-readable format. This page outlines the key
                            requirements for maintaining CRA-compliant SBOMs.
                        </p>
                    </div>

                    {/* Section Cards */}
                    <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#333', margin: '28px 0 16px' }}>
                        Key Requirements
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
                            CRA Recital 78 & Annex I — SBOM Obligations
                        </h3>
                        <ul style={{ margin: 0, paddingLeft: '20px', color: '#444', fontSize: '14px', lineHeight: 1.8 }}>
                            <li><strong>Component identification</strong> — the technical documentation must include an SBOM identifying the top-level dependencies of the product, generated in a commonly used and machine-readable format.</li>
                            <li><strong>Annex I Part II(1)</strong> — products must be delivered with information about the components and dependencies included, to enable users to identify known vulnerabilities.</li>
                            <li><strong>Supply chain transparency</strong> — manufacturers must exercise due diligence when integrating third-party components and verify that those components do not compromise the product's security.</li>
                            <li><strong>Availability</strong> — the SBOM must be made available to market surveillance authorities upon request, and relevant information should be provided to users to support vulnerability management.</li>
                        </ul>
                    </div>

                    <div style={{ marginBottom: '28px' }} />
                </div>
            </div>
        </div>
    );
};

export default SbomManagementPage;
