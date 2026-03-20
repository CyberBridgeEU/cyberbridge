import { DeploymentUnitOutlined } from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const sections = [
    {
        number: 1,
        title: 'Threat Modeling',
        description: 'Conduct and document systematic threat modeling for the product. Identify potential threat actors, attack vectors, and threat scenarios using established methodologies such as STRIDE, PASTA, or attack trees.'
    },
    {
        number: 2,
        title: 'Attack Surface Analysis',
        description: 'Map and document the product\'s attack surface, including all entry points, network interfaces, APIs, user inputs, and external integrations. Describe measures taken to minimise the attack surface.'
    },
    {
        number: 3,
        title: 'Security Architecture Decisions',
        description: 'Record key security architecture decisions, including chosen cryptographic algorithms, authentication mechanisms, access control models, and secure communication protocols. Document rationale and trade-offs for each decision.'
    },
    {
        number: 4,
        title: 'Data Flow Diagrams',
        description: 'Create data flow diagrams (DFDs) showing how data moves through the system, including data classification, storage locations, transmission channels, and processing points. Highlight where security controls are applied.'
    },
    {
        number: 5,
        title: 'Trust Boundaries',
        description: 'Identify and document all trust boundaries within the system architecture. Define where privilege levels change, where external inputs enter the system, and what validation and sanitisation controls exist at each boundary.'
    },
    {
        number: 6,
        title: 'Security Assumptions & Constraints',
        description: 'Document all security assumptions made during design (e.g., expected deployment environment, user behaviour, network trust levels) and constraints that limit security measures (e.g., hardware limitations, backwards compatibility).'
    }
];

const SecurityDesignDocPage = () => {
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
                            <DeploymentUnitOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Security Design Documentation</h1>
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
                            The <strong>Cyber Resilience Act (CRA)</strong> requires that products with digital elements
                            are designed and developed with security at their core. Security-by-design documentation
                            provides evidence that cybersecurity was considered from the earliest stages of product
                            development, and that architectural decisions were made to minimise risk and protect against
                            known threat categories.
                        </p>
                    </div>

                    {/* Section Cards */}
                    <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#333', margin: '28px 0 16px' }}>
                        Key Documentation Areas
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
                            CRA Article 13(1)–(2) — Secure Design Obligations
                        </h3>
                        <ul style={{ margin: 0, paddingLeft: '20px', color: '#444', fontSize: '14px', lineHeight: 1.8 }}>
                            <li><strong>Security by design and default</strong> — products must be designed, developed, and produced to ensure an appropriate level of cybersecurity, and must be delivered with a secure default configuration.</li>
                            <li><strong>Risk-based approach</strong> — the level of cybersecurity must be appropriate to the risk, taking into account the intended use and reasonably foreseeable conditions of use.</li>
                            <li><strong>Minimised attack surface</strong> — products must be designed to limit attack surfaces, including external interfaces, and to ensure that exploitable vulnerabilities can be addressed through security updates.</li>
                            <li><strong>Technical documentation</strong> — the technical file must include a description of the security design, architecture decisions, and how essential cybersecurity requirements are met.</li>
                        </ul>
                    </div>

                    <div style={{ marginBottom: '28px' }} />
                </div>
            </div>
        </div>
    );
};

export default SecurityDesignDocPage;
