// src/components/guided-tour/QuickStartTour.tsx
import { useEffect, useRef, useCallback } from 'react';
import Joyride, { type CallBackProps, type Step, ACTIONS, EVENTS, STATUS } from 'react-joyride';
import { useLocation } from 'wouter';
import useGuidedTourStore from '../../store/useGuidedTourStore';

interface QsStep extends Step {
    route: string;
    tabKey?: string;
}

const AMBER = '#f59e0b';

const tourSteps: QsStep[] = [
    {
        target: '[data-tour-id="qs-framework-page-header"]',
        title: 'Step 1: Add a Framework',
        content: 'Frameworks define the compliance standard you want to follow (e.g. CRA, ISO 27001, NIS2). Start here by selecting a framework template to adopt.',
        placement: 'bottom',
        disableBeacon: true,
        route: '/framework_management'
    },
    {
        target: '[data-tour-id="qs-framework-template-section"]',
        title: 'Select a Framework Template',
        content: 'Browse available templates and click "Add" to import a framework into your organisation. Each template comes with pre-defined chapters, objectives, and questions.',
        placement: 'bottom',
        disableBeacon: true,
        route: '/framework_management'
    },
    {
        target: '[data-tour-id="qs-assets-add-button"]',
        title: 'Step 2: Register an Asset',
        content: 'Register the digital products and assets your organisation needs to protect. Assets are linked to risks, controls, and compliance assessments.',
        placement: 'bottom',
        disableBeacon: true,
        route: '/assets',
        tabKey: 'assets'
    },
    {
        target: '[data-tour-id="qs-risk-add-button"]',
        title: 'Step 3: Register a Risk',
        content: 'Document risks that could impact your assets. Each risk can be assigned a severity, likelihood, and linked to controls that mitigate it.',
        placement: 'bottom',
        disableBeacon: true,
        route: '/risk_registration',
        tabKey: 'registry'
    },
    {
        target: '[data-tour-id="qs-control-add-button"]',
        title: 'Step 4: Register a Control',
        content: 'Controls are the safeguards and measures you put in place to mitigate risks. Link controls to risks and policies for a complete compliance chain.',
        placement: 'bottom',
        disableBeacon: true,
        route: '/control_registration',
        tabKey: 'registry'
    },
    {
        target: '[data-tour-id="qs-policy-add-button"]',
        title: 'Step 5: Create a Policy',
        content: 'Policies formalise your organisation\'s security rules. Create policies and link them to frameworks, objectives, and controls.',
        placement: 'bottom',
        disableBeacon: true,
        route: '/policies_registration',
        tabKey: 'policies'
    },
    {
        target: '[data-tour-id="qs-assessment-create-card"]',
        title: 'Step 6: Run an Assessment',
        content: 'Assessments evaluate your compliance against a framework. Use this card to create a new assessment -- select a framework, choose an assessment type, and answer the questions to measure your compliance posture.',
        placement: 'left',
        disableBeacon: true,
        route: '/assessments'
    },
    {
        target: '[data-tour-id="qs-objectives-page-header"]',
        title: 'Step 7: Objectives Checklist',
        content: 'The Objectives Checklist lets you review and track the compliance objectives defined in your framework chapters.',
        placement: 'bottom',
        disableBeacon: true,
        route: '/objectives_checklist'
    },
    {
        target: '[data-tour-id="qs-objectives-framework-select"]',
        title: 'Select Your Framework',
        content: 'Choose a framework to view its chapters and objectives. Each objective can be marked with a compliance status and linked to policies.',
        placement: 'bottom',
        disableBeacon: true,
        route: '/objectives_checklist'
    },
    {
        target: '[data-tour-id="qs-objectives-content-area"]',
        title: 'Tour Complete!',
        content: 'Once a framework is selected, its chapters and objectives appear here. Update compliance statuses, assign policies, and track your progress. You\'ve completed the Quick Start walkthrough -- you now know the 7-step workflow: Frameworks > Assets > Risks > Controls > Policies > Assessments > Objectives.',
        placement: 'top',
        disableBeacon: true,
        route: '/objectives_checklist'
    }
];

// Valid routes the tour visits
const TOUR_ROUTES = new Set([
    '/framework_management',
    '/assets',
    '/risk_registration',
    '/control_registration',
    '/policies_registration',
    '/assessments',
    '/objectives_checklist'
]);

const QuickStartTour: React.FC = () => {
    const [location, setLocation] = useLocation();
    const {
        qsIsRunning,
        qsStepIndex,
        qsIsNavigating,
        setQsStepIndex,
        setQsIsNavigating,
        stopQuickStartTour,
        completeQuickStartTour
    } = useGuidedTourStore();

    const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const isHandlingStepRef = useRef(false);
    // Track whether the tour initiated the current navigation
    const tourNavigatedRef = useRef(false);
    // Signal that we should navigate to /home after qsIsRunning becomes false
    const shouldNavigateHomeRef = useRef(false);

    const clearPollTimer = useCallback(() => {
        if (pollTimerRef.current) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
        }
    }, []);

    // Activate the correct Ant Design tab for steps that need it
    const activateTab = useCallback((tabKey: string) => {
        const tab = document.querySelector(`.ant-tabs-tab[data-node-key="${tabKey}"]`) as HTMLElement;
        if (tab) {
            tab.click();
        }
    }, []);

    // Poll for a DOM target to appear, then call onReady
    const pollForTarget = useCallback((step: QsStep, onReady: () => void) => {
        clearPollTimer();
        let attempts = 0;
        const maxAttempts = 20; // 200ms * 20 = 4s

        pollTimerRef.current = setInterval(() => {
            attempts++;

            // Activate tab if needed on every poll (component may mount late)
            if (step.tabKey) {
                activateTab(step.tabKey);
            }

            const target = typeof step.target === 'string'
                ? document.querySelector(step.target)
                : null;

            if (target) {
                clearPollTimer();
                onReady();
            } else if (attempts >= maxAttempts) {
                clearPollTimer();
                // Resume anyway -- Joyride will show TARGET_NOT_FOUND
                onReady();
            }
        }, 200);
    }, [clearPollTimer, activateTab]);

    // Ensure we're on the correct page for the current step
    // This fires when the tour starts or when the step changes after navigation
    useEffect(() => {
        if (!qsIsRunning || qsIsNavigating || shouldNavigateHomeRef.current) return;

        const step = tourSteps[qsStepIndex];
        if (!step) return;

        if (location !== step.route) {
            // Need to navigate to the step's page
            setQsIsNavigating(true);
            tourNavigatedRef.current = true;
            setLocation(step.route);
        } else {
            // Already on the right page -- activate tab and poll for target
            if (step.tabKey) {
                activateTab(step.tabKey);
            }
            // Quick check if target exists, poll if not
            const target = typeof step.target === 'string'
                ? document.querySelector(step.target)
                : null;
            if (!target) {
                setQsIsNavigating(true);
                pollForTarget(step, () => {
                    setQsIsNavigating(false);
                });
            }
        }
    }, [qsIsRunning, qsStepIndex, qsIsNavigating, location, setLocation, setQsIsNavigating, activateTab, pollForTarget]);

    // When location changes while navigating, poll for the target
    useEffect(() => {
        if (!qsIsRunning || !qsIsNavigating || shouldNavigateHomeRef.current) return;

        const step = tourSteps[qsStepIndex];
        if (!step) return;

        // We've arrived at the correct route
        if (location === step.route) {
            pollForTarget(step, () => {
                setQsIsNavigating(false);
            });
        }
    }, [location, qsIsRunning, qsIsNavigating, qsStepIndex, pollForTarget, setQsIsNavigating]);

    // Detect manual navigation away from tour routes
    useEffect(() => {
        if (!qsIsRunning || shouldNavigateHomeRef.current) return;

        // If the tour initiated this navigation, mark it consumed and skip
        if (tourNavigatedRef.current) {
            tourNavigatedRef.current = false;
            return;
        }

        // If navigating and the location changed, that's the tour navigating
        if (qsIsNavigating) return;

        // Check if user manually navigated to a non-tour route
        if (!TOUR_ROUTES.has(location)) {
            clearPollTimer();
            stopQuickStartTour();
        }
    }, [location, qsIsRunning, qsIsNavigating, stopQuickStartTour, clearPollTimer]);

    // Navigate to /home after the tour finishes and qsIsRunning is reflected as false
    useEffect(() => {
        if (!qsIsRunning && shouldNavigateHomeRef.current) {
            shouldNavigateHomeRef.current = false;
            setLocation('/home');
        }
    }, [qsIsRunning, setLocation]);

    // Clear poll timer when the tour stops running
    useEffect(() => {
        if (!qsIsRunning) {
            clearPollTimer();
        }
    }, [qsIsRunning, clearPollTimer]);

    const finishTour = useCallback(() => {
        clearPollTimer();
        shouldNavigateHomeRef.current = true;
        completeQuickStartTour();
        setLocation('/home');
    }, [clearPollTimer, completeQuickStartTour, setLocation]);

    const exitTour = useCallback(() => {
        clearPollTimer();
        shouldNavigateHomeRef.current = true;
        stopQuickStartTour();
        setLocation('/home');
    }, [clearPollTimer, stopQuickStartTour, setLocation]);

    const handleCallback = useCallback((data: CallBackProps) => {
        // Ignore stale callbacks after the tour has stopped
        if (!useGuidedTourStore.getState().qsIsRunning) return;

        const { action, index, type, status } = data;

        // Tour finished or skipped
        if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
            finishTour();
            return;
        }

        // Handle close action (X button or "Exit Tour")
        if (action === ACTIONS.CLOSE) {
            exitTour();
            return;
        }

        // Handle step navigation
        if (type === EVENTS.STEP_AFTER) {
            if (isHandlingStepRef.current) return;
            isHandlingStepRef.current = true;

            const nextIndex = action === ACTIONS.PREV ? index - 1 : index + 1;

            if (nextIndex < 0) {
                isHandlingStepRef.current = false;
                return;
            }

            // Last step completed -- finish the tour
            if (nextIndex >= tourSteps.length) {
                isHandlingStepRef.current = false;
                finishTour();
                return;
            }

            const nextStep = tourSteps[nextIndex];
            const currentStep = tourSteps[index];

            if (nextStep.route !== currentStep.route) {
                // Cross-page navigation: set navigating flag, update step
                // The useEffect above will handle the actual navigation
                setQsIsNavigating(true);
                tourNavigatedRef.current = true;
                setQsStepIndex(nextIndex);
                setLocation(nextStep.route);
                isHandlingStepRef.current = false;
            } else {
                // Same route -- activate tab if needed and advance
                if (nextStep.tabKey) {
                    activateTab(nextStep.tabKey);
                }
                setQsStepIndex(nextIndex);
                isHandlingStepRef.current = false;
            }
            return;
        }

        // Handle target not found -- poll and retry
        if (type === EVENTS.TARGET_NOT_FOUND) {
            // If this is the last step, just finish the tour instead of polling
            if (index >= tourSteps.length - 1) {
                finishTour();
                return;
            }
            const step = tourSteps[index];
            if (step) {
                setQsIsNavigating(true);
                pollForTarget(step, () => {
                    setQsIsNavigating(false);
                });
            }
        }
    }, [finishTour, exitTour, setLocation, setQsStepIndex, setQsIsNavigating, pollForTarget, activateTab]);

    if (!qsIsRunning) return null;

    return (
        <Joyride
            steps={tourSteps}
            run={qsIsRunning && !qsIsNavigating}
            stepIndex={qsStepIndex}
            continuous
            showSkipButton
            showProgress
            callback={handleCallback}
            locale={{
                back: 'Back',
                close: 'Close',
                last: 'Finish Tour',
                next: 'Next',
                skip: 'Exit Tour'
            }}
            styles={{
                options: {
                    primaryColor: AMBER,
                    textColor: '#262626',
                    backgroundColor: '#ffffff',
                    arrowColor: '#ffffff',
                    overlayColor: 'rgba(0, 0, 0, 0.5)',
                    zIndex: 10000
                },
                tooltip: {
                    borderRadius: '12px',
                    padding: '20px',
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)'
                },
                tooltipTitle: {
                    fontSize: '16px',
                    fontWeight: 700
                },
                tooltipContent: {
                    fontSize: '14px',
                    lineHeight: '1.6',
                    padding: '12px 0'
                },
                buttonNext: {
                    borderRadius: '8px',
                    fontSize: '13px',
                    fontWeight: 600,
                    padding: '8px 16px',
                    backgroundColor: AMBER
                },
                buttonBack: {
                    color: '#8c8c8c',
                    fontSize: '13px',
                    fontWeight: 500
                },
                buttonSkip: {
                    color: '#bfbfbf',
                    fontSize: '12px'
                },
                spotlight: {
                    borderRadius: '12px'
                }
            }}
        />
    );
};

export default QuickStartTour;
