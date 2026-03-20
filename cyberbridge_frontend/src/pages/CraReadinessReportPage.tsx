import { useRef, useEffect } from 'react';
import { useLocation } from 'wouter';
import useCraReadinessStore from '../store/useCraReadinessStore';
import { exportToPdf } from '../utils/pdfUtils';
import Sidebar from '../components/Sidebar';
import { useMenuHighlighting } from '../utils/menuUtils';

function getScoreLabel(score: number): { label: string; className: string } {
    if (score >= 76) return { label: 'High', className: 'high' };
    if (score >= 51) return { label: 'Moderate', className: 'moderate' };
    if (score >= 26) return { label: 'Low', className: 'low' };
    return { label: 'Critical', className: 'critical' };
}

function getRecommendations(category: string, score: number): string[] {
    if (score >= 76) {
        return [
            `Your ${category.toLowerCase()} practices are strong. Continue maintaining current processes and stay updated with evolving CRA requirements.`,
            'Consider pursuing formal certification to demonstrate compliance to customers and regulators.',
        ];
    }
    if (score >= 51) {
        return [
            `Your ${category.toLowerCase()} practices show moderate readiness. Identify and address the gaps highlighted in this assessment.`,
            'Develop a structured improvement plan with clear timelines and responsibilities.',
            'Consider engaging external consultants to accelerate your compliance journey.',
        ];
    }
    if (score >= 26) {
        return [
            `Your ${category.toLowerCase()} practices need significant improvement to meet CRA requirements.`,
            'Prioritise establishing formal processes and documentation for all key areas.',
            'Invest in staff training and consider adopting industry-standard frameworks and tools.',
            'Engage with CRA compliance specialists to develop a comprehensive remediation roadmap.',
        ];
    }
    return [
        `Your ${category.toLowerCase()} practices require urgent attention to achieve CRA compliance.`,
        'Immediate action is needed to establish foundational cybersecurity processes.',
        'Consider a full gap analysis with qualified cybersecurity professionals.',
        'Develop and implement a comprehensive cybersecurity programme covering all CRA essential requirements.',
        'Allocate dedicated resources and budget for compliance activities.',
    ];
}

export default function CraReadinessReportPage() {
    const [location, setLocation] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const reportRef = useRef<HTMLDivElement>(null);
    const { readinessScores, data } = useCraReadinessStore();

    useEffect(() => {
        if (!readinessScores) {
            setLocation('/cra-readiness-assessment');
        }
    }, [readinessScores, setLocation]);

    if (!readinessScores) return null;

    const handleDownloadPdf = () => {
        exportToPdf(reportRef.current, 'CRA_Readiness_Assessment_Report');
    };

    const overallInfo = getScoreLabel(readinessScores.overall);
    const riskInfo = getScoreLabel(readinessScores.riskAssessment);
    const vulnInfo = getScoreLabel(readinessScores.vulnerabilities);
    const docInfo = getScoreLabel(readinessScores.documentation);

    return (
        <div className={'page-parent'}>
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div className={'page-content'}>
                <div className="cra-report-page">
                    <div className="cra-report-actions">
                        <button className="cra-btn-back" onClick={() => setLocation('/cra-readiness-assessment')}>
                            Go Back
                        </button>
                        <button className="cra-btn-continue" onClick={handleDownloadPdf}>
                            Download PDF
                        </button>
                        <button className="cra-btn-login" onClick={() => setLocation('/assessments')}>
                            Back to Assessments
                        </button>
                    </div>

                    <div ref={reportRef} className="cra-report-container">
                <h1 className="cra-report-title">CRA Readiness Assessment Report</h1>
                <p className="cra-report-subtitle">
                    Assessment for: <strong>{(data.companyInfo.companyName as string) || 'N/A'}</strong>
                    {data.productInfo.craCategory && <> — Category: <strong>{data.productInfo.craCategory as string}</strong></>}
                </p>

                <section className="cra-report-section">
                    <h2>Report Introduction</h2>
                    <p>
                        This CRA Readiness Assessment evaluates your organisation's preparedness for compliance with the
                        Cyber Resilience Act (CRA). The assessment covers three key areas: Risk Assessment, Vulnerability
                        Management, and Documentation. Each area is scored based on your responses to determine your current
                        readiness level and identify areas for improvement.
                    </p>
                    <p style={{ marginTop: '12px' }}>
                        <strong>Scoring methodology:</strong> Toggle questions (Yes/No) and Likert scale responses
                        (Strongly Disagree to Strongly Agree) are scored to calculate a percentage readiness for each category.
                        General information fields are not scored but provide important context.
                    </p>
                </section>

                {/* Overall Score */}
                <section className="cra-report-section">
                    <h2>Overall Readiness Score</h2>
                    <div className={`cra-readiness-score ${overallInfo.className}`}>
                        <div className="cra-readiness-score-value">{readinessScores.overall}%</div>
                        <div className="cra-readiness-score-label">{overallInfo.label} Readiness</div>
                    </div>
                </section>

                {/* Category Breakdown */}
                <section className="cra-report-section">
                    <h2>Category Breakdown</h2>
                    <div className="cra-readiness-categories">
                        <div className={`cra-readiness-category ${riskInfo.className}`}>
                            <div className="cra-readiness-category-score">{readinessScores.riskAssessment}%</div>
                            <div className="cra-readiness-category-label">Risk Assessment</div>
                            <div className="cra-readiness-category-status">{riskInfo.label}</div>
                        </div>
                        <div className={`cra-readiness-category ${vulnInfo.className}`}>
                            <div className="cra-readiness-category-score">{readinessScores.vulnerabilities}%</div>
                            <div className="cra-readiness-category-label">Vulnerabilities</div>
                            <div className="cra-readiness-category-status">{vulnInfo.label}</div>
                        </div>
                        <div className={`cra-readiness-category ${docInfo.className}`}>
                            <div className="cra-readiness-category-score">{readinessScores.documentation}%</div>
                            <div className="cra-readiness-category-label">Documentation</div>
                            <div className="cra-readiness-category-status">{docInfo.label}</div>
                        </div>
                    </div>
                </section>

                {/* Detailed Analysis */}
                <section className="cra-report-section">
                    <h2>Risk Assessment Analysis</h2>
                    <p>
                        The Risk Assessment category evaluates your organisation's approach to identifying, managing, and mitigating
                        cybersecurity risks across the product lifecycle. This includes risk management processes, security testing
                        practices, secure configuration, and security controls.
                    </p>
                    <div className="cra-report-analysis-item">
                        <h3>Score: {readinessScores.riskAssessment}% — {riskInfo.label}</h3>
                        <p><strong>Recommendations:</strong></p>
                        <ul style={{ margin: '8px 0 0 20px', color: '#475569', fontSize: '14px', lineHeight: '1.8' }}>
                            {getRecommendations('Risk Assessment', readinessScores.riskAssessment).map((rec, i) => (
                                <li key={i}>{rec}</li>
                            ))}
                        </ul>
                    </div>
                </section>

                <section className="cra-report-section">
                    <h2>Vulnerabilities Analysis</h2>
                    <p>
                        The Vulnerabilities category assesses your organisation's capability to identify, manage, and disclose
                        product vulnerabilities. This includes post-market testing, coordinated disclosure processes, and
                        security patch distribution.
                    </p>
                    <div className="cra-report-analysis-item">
                        <h3>Score: {readinessScores.vulnerabilities}% — {vulnInfo.label}</h3>
                        <p><strong>Recommendations:</strong></p>
                        <ul style={{ margin: '8px 0 0 20px', color: '#475569', fontSize: '14px', lineHeight: '1.8' }}>
                            {getRecommendations('Vulnerability Management', readinessScores.vulnerabilities).map((rec, i) => (
                                <li key={i}>{rec}</li>
                            ))}
                        </ul>
                    </div>
                </section>

                <section className="cra-report-section">
                    <h2>Documentation Analysis</h2>
                    <p>
                        The Documentation category evaluates the completeness of your product documentation, including the
                        Software Bill of Materials (SBOM) and technical documentation required by the CRA.
                    </p>
                    <div className="cra-report-analysis-item">
                        <h3>Score: {readinessScores.documentation}% — {docInfo.label}</h3>
                        <p><strong>Recommendations:</strong></p>
                        <ul style={{ margin: '8px 0 0 20px', color: '#475569', fontSize: '14px', lineHeight: '1.8' }}>
                            {getRecommendations('Documentation', readinessScores.documentation).map((rec, i) => (
                                <li key={i}>{rec}</li>
                            ))}
                        </ul>
                    </div>
                </section>

                {/* Company Summary */}
                <section className="cra-report-section">
                    <h2>Assessment Context</h2>
                    <div className="cra-report-analysis-item">
                        <h3>Company &amp; Product Details</h3>
                        <table style={{ width: '100%', fontSize: '14px', color: '#475569' }}>
                            <tbody>
                                <tr><td style={{ padding: '6px 12px', fontWeight: 600 }}>Company</td><td style={{ padding: '6px 12px' }}>{(data.companyInfo.companyName as string) || '—'}</td></tr>
                                <tr><td style={{ padding: '6px 12px', fontWeight: 600 }}>Contact</td><td style={{ padding: '6px 12px' }}>{(data.companyInfo.contactName as string) || '—'}</td></tr>
                                <tr><td style={{ padding: '6px 12px', fontWeight: 600 }}>Company Size</td><td style={{ padding: '6px 12px' }}>{(data.companyInfo.companySize as string) || '—'}</td></tr>
                                <tr><td style={{ padding: '6px 12px', fontWeight: 600 }}>Country</td><td style={{ padding: '6px 12px' }}>{(data.companyInfo.country as string) || '—'}</td></tr>
                                <tr><td style={{ padding: '6px 12px', fontWeight: 600 }}>CRA Category</td><td style={{ padding: '6px 12px' }}>{(data.productInfo.craCategory as string) || '—'}</td></tr>
                                <tr><td style={{ padding: '6px 12px', fontWeight: 600 }}>Product Type</td><td style={{ padding: '6px 12px' }}>{(data.productInfo.productType as string) || '—'}</td></tr>
                            </tbody>
                        </table>
                    </div>
                </section>

                <section className="cra-report-section disclaimer">
                    <h2>Disclaimer</h2>
                    <p>
                        This readiness assessment is provided for informational purposes only and does not constitute legal advice
                        or a formal compliance certification. The scores reflect your self-reported responses and may not represent
                        your actual compliance status. The Cyber Resilience Act has specific technical requirements that should be
                        assessed by qualified professionals. CyberBridge recommends engaging with qualified legal and cybersecurity
                        compliance professionals to confirm your product's regulatory obligations and develop a comprehensive
                        compliance programme.
                    </p>
                </section>
                </div>
            </div>
        </div>
    </div>
    );
}
