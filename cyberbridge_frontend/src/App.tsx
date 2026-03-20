import './App.css'
import { Route, Switch, Redirect } from "wouter"
import { useEffect } from "react"
import useSettingsStore from "./store/useSettingsStore.ts"
import { QuickStartTour } from "./components/guided-tour"
import HomePage from "./pages/HomePage.tsx"
import NotFoundPage from "./pages/NotFoundPage.tsx"
import LoginPage from "./pages/LoginPage.tsx"
import RegisterPage from "./pages/RegisterPage.tsx"
import ProtectedRoute from "./components/ProtectedRoute.tsx"
import AssessmentsPage from "./pages/AssessmentsPage.tsx";
import UserManagementPage from "./pages/UserManagementPage.tsx";
import OrganizationsPage from "./pages/OrganizationsPage.tsx";
import UsersPage from "./pages/UsersPage.tsx";
import ManageFrameworks from "./pages/FrameworkManagementPage.tsx";
import ChaptersObjectivesPage from "./pages/ChaptersObjectivesPage.tsx";
import FrameworkQuestionsPage from "./pages/FrameworkQuestionsPage.tsx";
import FrameworkUpdatesPage from "./pages/FrameworkUpdatesPage.tsx";
import PolicyRegistrationPage from "./pages/PolicyRegistrationPage.tsx";
import RiskRegistrationPage from "./pages/RiskRegistrationPage.tsx";
import UpdatePasswordPage from "./pages/UpdatePassword.tsx";
import SecurityScannersPage from "./pages/SecurityScannersPage.tsx";
import SemgrepPage from "./pages/SemgrepPage.tsx";
import OsvPage from "./pages/OsvPage.tsx";
import SyftPage from "./pages/SyftPage.tsx";
import DocumentationPage from "./pages/DocumentationPage.tsx";
import ObjectivesChecklistPage from "./pages/ObjectivesChecklistPage.tsx";
import SettingsPage from "./pages/SettingsPage.tsx";
import AdminAreaPage from "./pages/AdminAreaPage.tsx";
import HistoryAreaPage from "./pages/HistoryAreaPage.tsx";
import CorrelationsPage from "./pages/CorrelationsPage.tsx";
import ProfilePage from "./pages/ProfilePage.tsx";
import ArchitecturePage from "./pages/ArchitecturePage.tsx";
import EvidencePage from "./pages/EvidencePage.tsx";
import AuditEngagementsPage from "./pages/AuditEngagementsPage.tsx";
import AuditorLoginPage from "./pages/AuditorLoginPage.tsx";
import AuditorReviewPage from "./pages/AuditorReviewPage.tsx";
import BackgroundJobsPage from "./pages/BackgroundJobsPage.tsx";
import AssetsPage from "./pages/AssetsPage.tsx";
import ControlRegistrationPage from "./pages/ControlRegistrationPage.tsx";
import ControlsLibraryPage from "./pages/ControlsLibraryPage.tsx";
import ComplianceChainLinksPage from "./pages/ComplianceChainLinksPage.tsx";
import ComplianceChainMapPage from "./pages/ComplianceChainMapPage.tsx"
import ScanFindingsPage from "./pages/ScanFindingsPage.tsx";
import ComplianceAdvisorPage from "./pages/ComplianceAdvisorPage.tsx";
import IncidentRegistrationPage from "./pages/IncidentRegistrationPage.tsx";
import RiskAssessmentPage from "./pages/RiskAssessmentPage.tsx";
import SSOCallbackPage from "./pages/SSOCallbackPage.tsx";
import VerifySuccessPage from "./pages/VerifySuccessPage.tsx";
import CraScopeAssessmentPage from "./pages/CraScopeAssessmentPage.tsx";
import CraScopeReportPage from "./pages/CraScopeReportPage.tsx";
import CraReadinessAssessmentPage from "./pages/CraReadinessAssessmentPage.tsx";
import CraReadinessReportPage from "./pages/CraReadinessReportPage.tsx";
import ForceChangePasswordPage from "./pages/ForceChangePasswordPage.tsx";
import EuDocPage from "./pages/EuDocPage.tsx";
import PatchSupportPolicyPage from "./pages/PatchSupportPolicyPage.tsx";
import VulnerabilityDisclosurePolicyPage from "./pages/VulnerabilityDisclosurePolicyPage.tsx";
import SbomManagementPage from "./pages/SbomManagementPage.tsx";
import SecureSdlcEvidencePage from "./pages/SecureSdlcEvidencePage.tsx";
import SecurityDesignDocPage from "./pages/SecurityDesignDocPage.tsx";
import DependencyPolicyPage from "./pages/DependencyPolicyPage.tsx"
import CEMarkingChecklistPage from "./pages/CEMarkingChecklistPage.tsx"
import SecurityAdvisoriesPage from "./pages/SecurityAdvisoriesPage.tsx";
import GapAnalysisPage from "./pages/GapAnalysisPage.tsx";
import DarkWebDashboardPage from "./pages/DarkWebDashboardPage.tsx";
import DarkWebScansPage from "./pages/DarkWebScansPage.tsx";
import DarkWebScanDetailPage from "./pages/DarkWebScanDetailPage.tsx";
import DarkWebReportsPage from "./pages/DarkWebReportsPage.tsx";
import DarkWebSettingsPage from "./pages/DarkWebSettingsPage.tsx";
import CtiOverviewPage from "./pages/CtiOverviewPage.tsx";
import CtiThreatIntelPage from "./pages/CtiThreatIntelPage.tsx";
import CtiNetworkPage from "./pages/CtiNetworkPage.tsx";
import CtiWebVulnsPage from "./pages/CtiWebVulnsPage.tsx";
import CtiCodeAnalysisPage from "./pages/CtiCodeAnalysisPage.tsx";
import CtiDependenciesPage from "./pages/CtiDependenciesPage.tsx";

function App() {
    const { loadSettings } = useSettingsStore();

    // Load settings from localStorage on app initialization
    useEffect(() => {
        loadSettings();
    }, [loadSettings]);

    return (
        <div>
            <main>
                <Switch>
                    <Route path="/">
                        <Redirect to="/home" />
                    </Route>
                    <Route path="/login" component={LoginPage} />
                    <Route path="/register" component={RegisterPage} />

                    {/* SSO Callback Route (public) */}
                    <Route path="/sso/callback" component={SSOCallbackPage} />

                    {/* Email Verification Result (public) */}
                    <Route path="/verify-success" component={VerifySuccessPage} />

                    {/* Auditor Portal Routes (separate authentication) */}
                    <Route path="/auditor/login" component={AuditorLoginPage} />
                    <Route path="/auditor/review" component={AuditorReviewPage} />

                    {/* Force Change Password (public - requires token but not full protection) */}
                    <Route path="/force-change-password" component={ForceChangePasswordPage} />

                    {/* CRA Assessment Routes (Protected) */}
                    <Route path="/cra-scope-assessment">
                        <ProtectedRoute>
                            <CraScopeAssessmentPage />
                        </ProtectedRoute>
                    </Route>
                    <Route path="/cra-scope-report">
                        <ProtectedRoute>
                            <CraScopeReportPage />
                        </ProtectedRoute>
                    </Route>
                    <Route path="/cra-readiness-assessment">
                        <ProtectedRoute>
                            <CraReadinessAssessmentPage />
                        </ProtectedRoute>
                    </Route>
                    <Route path="/cra-readiness-report">
                        <ProtectedRoute>
                            <CraReadinessReportPage />
                        </ProtectedRoute>
                    </Route>

                    {/* Protected Routes */}
                    <Route path="/home">
                        <ProtectedRoute>
                            <HomePage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/assessments">
                        <ProtectedRoute>
                            <AssessmentsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/policies_registration">
                        <ProtectedRoute>
                            <PolicyRegistrationPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/architecture">
                        <ProtectedRoute>
                            <ArchitecturePage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/evidence">
                        <ProtectedRoute>
                            <EvidencePage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/assets">
                        <ProtectedRoute>
                            <AssetsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/risk_registration">
                        <ProtectedRoute>
                            <RiskRegistrationPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/risk_assessment/:riskId">
                        <ProtectedRoute>
                            <RiskAssessmentPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/risk_assessment">
                        <ProtectedRoute>
                            <RiskAssessmentPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/incidents">
                        <ProtectedRoute>
                            <IncidentRegistrationPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/control_registration">
                        <ProtectedRoute>
                            <ControlRegistrationPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/controls_library">
                        <ProtectedRoute>
                            <ControlsLibraryPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/compliance_chain_links">
                        <ProtectedRoute>
                            <ComplianceChainLinksPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/compliance_chain_map">
                        <ProtectedRoute>
                            <ComplianceChainMapPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/gap_analysis">
                        <ProtectedRoute>
                            <GapAnalysisPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/objectives_checklist">
                        <ProtectedRoute>
                            <ObjectivesChecklistPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/update_password">
                        <ProtectedRoute>
                            <UpdatePasswordPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/security_scanners">
                        <ProtectedRoute>
                            <SecurityScannersPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/code_analysis">
                        <ProtectedRoute>
                            <SemgrepPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/dependency_check">
                        <ProtectedRoute>
                            <OsvPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/sbom_generator">
                        <ProtectedRoute>
                            <SyftPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/scan_findings">
                        <ProtectedRoute>
                            <ScanFindingsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/eu_declaration_of_conformity">
                        <ProtectedRoute requiresCRAMode>
                            <EuDocPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/patch_support_policy">
                        <ProtectedRoute requiresCRAMode>
                            <PatchSupportPolicyPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/vulnerability_disclosure_policy">
                        <ProtectedRoute requiresCRAMode>
                            <VulnerabilityDisclosurePolicyPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/sbom_management">
                        <ProtectedRoute requiresCRAMode>
                            <SbomManagementPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/secure_sdlc_evidence">
                        <ProtectedRoute requiresCRAMode>
                            <SecureSdlcEvidencePage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/security_design_documentation">
                        <ProtectedRoute requiresCRAMode>
                            <SecurityDesignDocPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/dependency_policy">
                        <ProtectedRoute requiresCRAMode>
                            <DependencyPolicyPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/ce_marking_checklist">
                        <ProtectedRoute requiresCRAMode>
                            <CEMarkingChecklistPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/advisories">
                        <ProtectedRoute>
                            <SecurityAdvisoriesPage />
                        </ProtectedRoute>
                    </Route>

                    {/* CTI Dashboard Routes */}
                    <Route path="/cti/overview">
                        <ProtectedRoute>
                            <CtiOverviewPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/cti/threat-intel">
                        <ProtectedRoute>
                            <CtiThreatIntelPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/cti/network">
                        <ProtectedRoute>
                            <CtiNetworkPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/cti/web-vulns">
                        <ProtectedRoute>
                            <CtiWebVulnsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/cti/code-analysis">
                        <ProtectedRoute>
                            <CtiCodeAnalysisPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/cti/dependencies">
                        <ProtectedRoute>
                            <CtiDependenciesPage />
                        </ProtectedRoute>
                    </Route>

                    {/* Dark Web Intelligence Routes */}
                    <Route path="/dark-web/dashboard">
                        <ProtectedRoute>
                            <DarkWebDashboardPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/dark-web/scans">
                        <ProtectedRoute>
                            <DarkWebScansPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/dark-web/scan/:scanId">
                        <ProtectedRoute>
                            <DarkWebScanDetailPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/dark-web/reports">
                        <ProtectedRoute>
                            <DarkWebReportsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/dark-web/settings">
                        <ProtectedRoute>
                            <DarkWebSettingsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/documentation">
                        <ProtectedRoute>
                            <DocumentationPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/framework_management">
                        <ProtectedRoute>
                            <ManageFrameworks />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/chapters_objectives">
                        <ProtectedRoute>
                            <ChaptersObjectivesPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/framework_questions">
                        <ProtectedRoute>
                            <FrameworkQuestionsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/framework_updates">
                        <ProtectedRoute>
                            <FrameworkUpdatesPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/compliance_advisor">
                        <ProtectedRoute>
                            <ComplianceAdvisorPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/user_management">
                        <ProtectedRoute>
                            <UserManagementPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/organizations">
                        <ProtectedRoute>
                            <OrganizationsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/users">
                        <ProtectedRoute>
                            <UsersPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/settings">
                        <ProtectedRoute>
                            <SettingsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/correlations">
                        <ProtectedRoute>
                            <CorrelationsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/admin">
                        <Redirect to="/users" />
                    </Route>

                    <Route path="/history">
                        <ProtectedRoute>
                            <HistoryAreaPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/profile">
                        <ProtectedRoute>
                            <ProfilePage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/audit-engagements">
                        <ProtectedRoute>
                            <AuditEngagementsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/background-jobs">
                        <ProtectedRoute>
                            <BackgroundJobsPage />
                        </ProtectedRoute>
                    </Route>

                    <Route path="/notfound">
                        <ProtectedRoute>
                            <NotFoundPage />
                        </ProtectedRoute>
                    </Route>

                    <Route>
                        <Redirect to="/notfound" />
                    </Route>
                </Switch>
            </main>
            <QuickStartTour />
        </div>
    )
}

export default App
