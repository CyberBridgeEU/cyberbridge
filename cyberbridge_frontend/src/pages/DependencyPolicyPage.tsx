import { BugOutlined } from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const sections = [
    {
        number: 1,
        title: 'Acceptable License Policy',
        description: 'Define which open-source and third-party licenses are approved for use in the product. Maintain an allow-list of accepted licenses and a deny-list of prohibited ones, with a review process for edge cases.'
    },
    {
        number: 2,
        title: 'Vulnerability Threshold Policy',
        description: 'Set maximum acceptable vulnerability severity thresholds for dependencies. Define blocking criteria (e.g., no critical/high CVEs in production dependencies) and time-bound remediation requirements for each severity level.'
    },
    {
        number: 3,
        title: 'Update Frequency Requirements',
        description: 'Establish minimum update cadences for third-party dependencies. Define how often dependencies must be reviewed for updates, and set maximum age thresholds before a dependency must be updated or replaced.'
    },
    {
        number: 4,
        title: 'Approved & Blocked Component List',
        description: 'Maintain a curated list of pre-approved components that have passed security review, and a blocked list of components with known issues. Include criteria for adding or removing components from each list.'
    },
    {
        number: 5,
        title: 'Transitive Dependency Management',
        description: 'Establish processes for monitoring and managing transitive (indirect) dependencies. Include tooling for full dependency tree visibility, vulnerability scanning of transitive dependencies, and pinning strategies.'
    },
    {
        number: 6,
        title: 'Supply Chain Risk Assessment',
        description: 'Conduct and document supply chain risk assessments for critical dependencies. Evaluate maintainer trust, project health metrics, bus factor, funding stability, and the potential impact of compromise on your product.'
    }
];

const DependencyPolicyPage = () => {
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
                            <BugOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Dependency Policy</h1>
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
                            The <strong>Cyber Resilience Act (CRA)</strong> places explicit obligations on manufacturers
                            to exercise due diligence when integrating third-party components into their products with
                            digital elements. This includes verifying that components do not compromise product security,
                            maintaining a clear inventory of all dependencies, and ensuring that vulnerabilities in
                            third-party code are identified and addressed promptly.
                        </p>
                    </div>

                    {/* Section Cards */}
                    <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#333', margin: '28px 0 16px' }}>
                        Key Policy Areas
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
                            CRA Annex I Part I(2) & Recital 78 — Third-Party Component Obligations
                        </h3>
                        <ul style={{ margin: 0, paddingLeft: '20px', color: '#444', fontSize: '14px', lineHeight: 1.8 }}>
                            <li><strong>Due diligence on components</strong> — manufacturers must exercise due diligence when integrating components from third parties, ensuring they do not compromise the cybersecurity of the product.</li>
                            <li><strong>Known vulnerability management</strong> — products must be delivered without known exploitable vulnerabilities in their components, and manufacturers must address new vulnerabilities without delay.</li>
                            <li><strong>SBOM requirement</strong> — the technical documentation must include an SBOM documenting at minimum the top-level dependencies, enabling identification and tracking of component vulnerabilities.</li>
                            <li><strong>Supply chain security</strong> — manufacturers are responsible for the security of third-party components they integrate, and must have processes to monitor and respond to vulnerabilities in those components.</li>
                        </ul>
                    </div>

                    <div style={{ marginBottom: '28px' }} />
                </div>
            </div>
        </div>
    );
};

export default DependencyPolicyPage;
