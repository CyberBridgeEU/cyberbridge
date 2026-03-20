import { SafetyOutlined } from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const sections = [
    {
        number: 1,
        title: 'Code Review Process',
        description: 'Document the systematic code review process, including peer review requirements, review checklists, approval workflows, and how security-relevant code changes are flagged for additional scrutiny.'
    },
    {
        number: 2,
        title: 'SAST / DAST Integration',
        description: 'Demonstrate integration of Static Application Security Testing (SAST) and Dynamic Application Security Testing (DAST) tools into the development pipeline. Include tool configuration, rulesets, and how findings are triaged and resolved.'
    },
    {
        number: 3,
        title: 'CI/CD Security Gates',
        description: 'Define security gates within the CI/CD pipeline that prevent insecure code from progressing to production. Include criteria for blocking builds, required scan pass rates, and exception handling procedures.'
    },
    {
        number: 4,
        title: 'Pre-Release Security Checklist',
        description: 'Maintain a documented pre-release security checklist that must be completed before each release. This should cover vulnerability assessment, dependency review, configuration hardening, and sign-off by security personnel.'
    },
    {
        number: 5,
        title: 'Dependency Scanning',
        description: 'Integrate automated dependency scanning (SCA) into the development lifecycle to identify known vulnerabilities in third-party components. Document the scanning frequency, remediation SLAs, and escalation paths for critical findings.'
    },
    {
        number: 6,
        title: 'Penetration Testing Records',
        description: 'Maintain records of penetration testing activities, including scope, methodology, findings, and remediation evidence. Testing should be conducted at appropriate intervals and before major releases.'
    }
];

const SecureSdlcEvidencePage = () => {
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
                            <SafetyOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Secure SDLC Evidence</h1>
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
                            The <strong>Cyber Resilience Act (CRA)</strong> requires manufacturers to design, develop, and
                            maintain products with digital elements following secure development lifecycle practices. The
                            technical documentation must include evidence that security has been systematically integrated
                            throughout the development process — from design through to release and ongoing maintenance.
                        </p>
                    </div>

                    {/* Section Cards */}
                    <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#333', margin: '28px 0 16px' }}>
                        Mandatory Evidence Areas
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
                            CRA Annex I Part I — Essential Cybersecurity Requirements
                        </h3>
                        <ul style={{ margin: 0, paddingLeft: '20px', color: '#444', fontSize: '14px', lineHeight: 1.8 }}>
                            <li><strong>Secure by design</strong> — products must be designed, developed, and produced to ensure an appropriate level of cybersecurity based on the risks, including during the development process.</li>
                            <li><strong>Risk-based testing</strong> — manufacturers must carry out adequate and effective testing and review of the product's security, proportionate to the risk.</li>
                            <li><strong>Documented processes</strong> — the technical documentation must describe the secure development procedures followed, including evidence of security testing, code reviews, and vulnerability management.</li>
                            <li><strong>Continuous improvement</strong> — security processes must be maintained and updated throughout the product's support period, not just at the time of initial market placement.</li>
                        </ul>
                    </div>

                    <div style={{ marginBottom: '28px' }} />
                </div>
            </div>
        </div>
    );
};

export default SecureSdlcEvidencePage;
