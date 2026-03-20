import { useRef, useEffect } from 'react';
import { useLocation } from 'wouter';
import useCraScopeStore from '../store/useCraScopeStore';
import { exportToPdf } from '../utils/pdfUtils';
import Sidebar from '../components/Sidebar';
import { useMenuHighlighting } from '../utils/menuUtils';

export default function CraScopeReportPage() {
    const [location, setLocation] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const reportRef = useRef<HTMLDivElement>(null);
    const { scopeResult, productDetails, marketInfo, companyDetails } = useCraScopeStore();

    useEffect(() => {
        if (!scopeResult) {
            setLocation('/cra-scope-assessment');
        }
    }, [scopeResult, setLocation]);

    if (!scopeResult) return null;

    const isInScope = scopeResult === 'IN_SCOPE';

    const handleDownloadPdf = () => {
        exportToPdf(reportRef.current, 'CRA_Scope_Assessment_Report');
    };

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
                        <button className="cra-btn-back" onClick={() => setLocation('/cra-scope-assessment')}>
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
                <h1 className="cra-report-title">Cyber Resilience Act Scope Assessment</h1>
                <p className="cra-report-subtitle">
                    Assessment for: <strong>{companyDetails.companyName || 'N/A'}</strong> — Product: <strong>{companyDetails.productName || 'N/A'}</strong>
                </p>

                <section className="cra-report-section">
                    <h2>Report Introduction</h2>
                    <p>
                        The Cyber Resilience Act (CRA) is a European Union regulation that establishes cybersecurity requirements
                        for products with digital elements. It aims to ensure that hardware and software products are placed on
                        the market with fewer vulnerabilities, and that manufacturers take security seriously throughout a
                        product's lifecycle. The CRA applies to all products with digital elements whose intended or reasonably
                        foreseeable use includes a direct or indirect logical or physical data connection to a device or network.
                    </p>
                </section>

                <section className="cra-report-section">
                    <h2>Why SMEs Should Care</h2>
                    <p>
                        Small and medium enterprises play a vital role in the EU's digital economy. The CRA helps SMEs by
                        establishing a level playing field for cybersecurity requirements, building customer trust, and
                        reducing long-term costs associated with security incidents. Non-compliance can result in significant
                        fines and market access restrictions.
                    </p>
                    <p style={{ marginTop: '12px' }}>
                        <strong>Transition timeline:</strong> The CRA entered into force on 10 December 2024. Manufacturers
                        will need to comply with the reporting obligations from 11 September 2026. The remaining obligations
                        will apply from 11 December 2027.
                    </p>
                </section>

                <section className="cra-report-section">
                    <div className={`cra-report-result ${isInScope ? 'in-scope' : 'out-scope'}`}>
                        <h2 style={{ margin: '0 0 8px 0' }}>Results Overview</h2>
                        <p style={{ fontSize: '18px', margin: 0 }}>
                            You are <strong>{isInScope ? 'IN SCOPE' : 'OUT OF SCOPE'}</strong> of the Cyber Resilience Act legislation.
                        </p>
                    </div>
                </section>

                <section className="cra-report-section">
                    <h2>Detailed Analysis</h2>

                    <div className="cra-report-analysis-item">
                        <h3>Is your product a digital product?</h3>
                        <p>Your answer: <strong>{productDetails.isDigitalProduct ? 'Yes' : 'No'}</strong></p>
                        <p>
                            {productDetails.isDigitalProduct
                                ? 'Your product qualifies as a "product with digital elements" under the CRA. This means it contains hardware and/or software components that are subject to the regulation\'s cybersecurity requirements.'
                                : 'Your product does not qualify as a "product with digital elements" under the CRA. Products without digital elements are not in scope of this regulation.'}
                        </p>
                    </div>

                    <div className="cra-report-analysis-item">
                        <h3>Does your product connect to a network or other devices?</h3>
                        <p>Your answer: <strong>{productDetails.connectsToNetwork ? 'Yes' : 'No'}</strong></p>
                        <p>
                            {productDetails.connectsToNetwork
                                ? 'Your product establishes data connections to networks or devices, which means it may be exposed to cybersecurity risks that the CRA aims to address. Network-connected products must implement appropriate security measures.'
                                : 'Your product does not connect to networks or other devices. While this reduces certain cybersecurity risks, other aspects of the CRA may still apply if the product contains digital elements.'}
                        </p>
                    </div>

                    <div className="cra-report-analysis-item">
                        <h3>Is your product standalone SaaS?</h3>
                        <p>Your answer: <strong>{productDetails.isSaaS ? 'Yes' : 'No'}</strong></p>
                        <p>
                            {productDetails.isSaaS
                                ? 'Your product is a standalone SaaS solution. Under the CRA, remote data processing solutions (including SaaS) are in scope when they are designed and developed by or on behalf of the manufacturer of the product with digital elements, and without which the product cannot perform one of its functions.'
                                : 'Your product is not a standalone SaaS solution. Traditional software and hardware products have their own set of requirements under the CRA.'}
                        </p>
                    </div>

                    <div className="cra-report-analysis-item">
                        <h3>Will you be placing or making available products on the EU market?</h3>
                        <p>Your answer: <strong>{marketInfo.euMarket ? 'Yes' : 'No'}</strong></p>
                        <p>
                            {marketInfo.euMarket
                                ? 'You intend to place or make your product available on the EU internal single market. This is a key criterion for the CRA to apply. All economic operators in the EU supply chain must comply with the relevant obligations.'
                                : 'You do not intend to place or make your product available on the EU market. The CRA only applies to products placed on or made available on the EU internal single market. Products exclusively sold outside the EU are not in scope.'}
                        </p>
                    </div>

                    <div className="cra-report-analysis-item">
                        <h3>Does your product comply with listed EU regulations?</h3>
                        <p>Your answer: <strong>{marketInfo.compliesWithRegulations ? 'Yes' : 'No'}</strong></p>
                        <p>
                            {marketInfo.compliesWithRegulations
                                ? 'Your product already complies with one or more of the listed EU regulations (MDR, IVDR, GSR, EASA, Defence Products Directive). Products that fall under these regulations are excluded from the scope of the CRA to avoid regulatory duplication.'
                                : 'Your product does not currently comply with any of the listed EU regulations that would exempt it from the CRA. You should assess whether the CRA requirements apply to your product.'}
                        </p>
                    </div>

                    <div className="cra-report-analysis-item">
                        <h3>Your role in the supply chain</h3>
                        <p>Your answer: <strong>{marketInfo.operatorRole || 'Not specified'}</strong></p>
                        <p>
                            {marketInfo.operatorRole === 'Manufacturer'
                                ? 'As a manufacturer, you bear the primary responsibility for ensuring your product meets all CRA cybersecurity requirements before placing it on the market. This includes conducting conformity assessments, maintaining technical documentation, and providing security updates.'
                                : marketInfo.operatorRole === 'Importer'
                                ? 'As an importer, you must ensure that the manufacturer has carried out the appropriate conformity assessment procedures and that the product bears the CE marking. You must also ensure the product is accompanied by the required documentation.'
                                : marketInfo.operatorRole === 'Distributor'
                                ? 'As a distributor, you must verify that the product bears the CE marking and is accompanied by the required documentation. You must also ensure appropriate storage and transport conditions do not jeopardize the product\'s compliance.'
                                : 'Your role in the supply chain has not been specified. The CRA assigns different obligations to manufacturers, importers, and distributors.'}
                        </p>
                    </div>
                </section>

                <section className="cra-report-section disclaimer">
                    <h2>Disclaimer</h2>
                    <p>
                        This assessment is provided for informational purposes only and does not constitute legal advice.
                        The determination of whether a product falls within the scope of the Cyber Resilience Act depends
                        on multiple factors and may require professional legal consultation. CyberBridge recommends engaging
                        with qualified legal and compliance professionals to confirm your product's regulatory obligations.
                    </p>
                </section>
                </div>
            </div>
        </div>
    </div>
    );
}
