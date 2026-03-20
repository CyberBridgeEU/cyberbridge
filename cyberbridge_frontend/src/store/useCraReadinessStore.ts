import { create } from 'zustand';

export type SectionKey =
    | 'companyInfo'
    | 'productInfo'
    | 'riskManagement'
    | 'testing'
    | 'secureConfig'
    | 'securityControls'
    | 'vulnManagement'
    | 'vulnDisclosure'
    | 'sbom'
    | 'productDocs';

export interface ReadinessScores {
    riskAssessment: number;
    vulnerabilities: number;
    documentation: number;
    overall: number;
}

interface SectionData {
    [key: string]: string | boolean;
}

interface CraReadinessState {
    currentSubStep: number;
    data: Record<SectionKey, SectionData>;
    readinessScores: ReadinessScores | null;
}

interface CraReadinessActions {
    nextStep: () => void;
    prevStep: () => void;
    setField: (section: SectionKey, field: string, value: string | boolean) => void;
    getField: (section: SectionKey, field: string) => string | boolean;
    calculateReadiness: () => void;
    resetAssessment: () => void;
}

const initialData: Record<SectionKey, SectionData> = {
    companyInfo: {
        companyName: '',
        contactName: '',
        companySize: '',
        country: '',
        sectors: '',
        languages: '',
        craImpact: '',
        staffTraining: '',
        productsOnMarket: '',
        newProducts: '',
    },
    productInfo: {
        craCategory: '',
        productType: '',
        marketChannel: '',
        importsComponents: false,
        lifecycleLength: '',
        containsOpenSource: false,
        intendedUse: '',
        keyFeatures: '',
        marketsForSale: '',
        harmonisedStandards: '',
        usesAI: false,
        processesGDPR: false,
    },
    riskManagement: {
        riskInLifecycle: false,
        formalMethodology: false,
        methodologies: '',
        internalOrExternal: '',
        formalReport: false,
        allPhasesAssessed: '',
        minimisingPriority: '',
    },
    testing: {
        testForVulnerabilities: false,
        vulnerabilityScanning: false,
        penetrationTesting: false,
        codeReviews: false,
        riskBasedTesting: false,
        standardisedDB: false,
        confidentNoVulnerabilities: '',
        systematicDocumenting: false,
    },
    secureConfig: {
        secureByDefault: false,
        secureConfigDocs: false,
        resetInstructions: false,
    },
    securityControls: {
        unauthorisedAccess: false,
        dataConfidentiality: false,
        dataIntegrity: false,
        dataAvailability: false,
        dosResilience: false,
        dataMinimised: false,
        noNegativeImpact: false,
        limitAttackSurfaces: '',
        reduceIncidentImpact: '',
        monitorActivity: false,
    },
    vulnManagement: {
        routineTestPostMarket: false,
        vulnScanningLifecycle: false,
        penTestLifecycle: false,
        codeReviewLifecycle: false,
        vulnTestOnUpdates: false,
        addressPromptly: '',
    },
    vulnDisclosure: {
        publiclyDisclose: false,
        disclosureMethod: '',
        coordinatedPolicy: false,
        contactAddress: false,
        otherMeasures: false,
        measuresDetails: '',
        secureDistribution: false,
        patchesNoDelay: false,
        patchesFreeOfCharge: false,
        patchesWithInfo: false,
    },
    sbom: {
        hasSBOM: false,
        sbomProcess: '',
        sbomFormat: false,
    },
    productDocs: {
        manufacturerDetails: false,
        vulnReportingContact: false,
        productIdentification: false,
        intendedUseDocs: false,
    },
};

// Scoring helpers
function scoreToggle(val: string | boolean): number {
    return val === true ? 1 : 0;
}

function scoreLikert(val: string | boolean): number {
    if (typeof val !== 'string') return 0;
    const map: Record<string, number> = {
        'Strongly Disagree': 0,
        'Disagree': 0.25,
        'Neutral': 0.5,
        'Agree': 0.75,
        'Strongly Agree': 1,
    };
    return map[val] ?? 0;
}

function scoreSectionFields(
    section: SectionData,
    scorableFields: { field: string; type: 'toggle' | 'likert' }[]
): number {
    if (scorableFields.length === 0) return 0;
    let total = 0;
    for (const { field, type } of scorableFields) {
        const val = section[field];
        total += type === 'likert' ? scoreLikert(val) : scoreToggle(val);
    }
    return total / scorableFields.length;
}

const useCraReadinessStore = create<CraReadinessState & CraReadinessActions>((set, get) => ({
    currentSubStep: 0,
    data: JSON.parse(JSON.stringify(initialData)),
    readinessScores: null,

    nextStep: () => {
        const { currentSubStep } = get();
        set({ currentSubStep: Math.min(currentSubStep + 1, 10) });
    },

    prevStep: () => {
        const { currentSubStep } = get();
        set({ currentSubStep: Math.max(currentSubStep - 1, 0) });
    },

    setField: (section, field, value) => {
        const { data } = get();
        set({
            data: {
                ...data,
                [section]: { ...data[section], [field]: value },
            },
        });
    },

    getField: (section, field) => {
        return get().data[section][field];
    },

    calculateReadiness: () => {
        const { data } = get();

        // Risk Assessment = riskManagement + testing + secureConfig + securityControls
        const riskManagementFields: { field: string; type: 'toggle' | 'likert' }[] = [
            { field: 'riskInLifecycle', type: 'toggle' },
            { field: 'formalMethodology', type: 'toggle' },
            { field: 'formalReport', type: 'toggle' },
            { field: 'allPhasesAssessed', type: 'likert' },
            { field: 'minimisingPriority', type: 'likert' },
        ];
        const testingFields: { field: string; type: 'toggle' | 'likert' }[] = [
            { field: 'testForVulnerabilities', type: 'toggle' },
            { field: 'vulnerabilityScanning', type: 'toggle' },
            { field: 'penetrationTesting', type: 'toggle' },
            { field: 'codeReviews', type: 'toggle' },
            { field: 'riskBasedTesting', type: 'toggle' },
            { field: 'standardisedDB', type: 'toggle' },
            { field: 'confidentNoVulnerabilities', type: 'likert' },
            { field: 'systematicDocumenting', type: 'toggle' },
        ];
        const secureConfigFields: { field: string; type: 'toggle' | 'likert' }[] = [
            { field: 'secureByDefault', type: 'toggle' },
            { field: 'secureConfigDocs', type: 'toggle' },
            { field: 'resetInstructions', type: 'toggle' },
        ];
        const securityControlsFields: { field: string; type: 'toggle' | 'likert' }[] = [
            { field: 'unauthorisedAccess', type: 'toggle' },
            { field: 'dataConfidentiality', type: 'toggle' },
            { field: 'dataIntegrity', type: 'toggle' },
            { field: 'dataAvailability', type: 'toggle' },
            { field: 'dosResilience', type: 'toggle' },
            { field: 'dataMinimised', type: 'toggle' },
            { field: 'noNegativeImpact', type: 'toggle' },
            { field: 'limitAttackSurfaces', type: 'likert' },
            { field: 'reduceIncidentImpact', type: 'likert' },
            { field: 'monitorActivity', type: 'toggle' },
        ];

        const riskScore1 = scoreSectionFields(data.riskManagement, riskManagementFields);
        const riskScore2 = scoreSectionFields(data.testing, testingFields);
        const riskScore3 = scoreSectionFields(data.secureConfig, secureConfigFields);
        const riskScore4 = scoreSectionFields(data.securityControls, securityControlsFields);
        const riskAssessment = ((riskScore1 + riskScore2 + riskScore3 + riskScore4) / 4) * 100;

        // Vulnerabilities = vulnManagement + vulnDisclosure
        const vulnManagementFields: { field: string; type: 'toggle' | 'likert' }[] = [
            { field: 'routineTestPostMarket', type: 'toggle' },
            { field: 'vulnScanningLifecycle', type: 'toggle' },
            { field: 'penTestLifecycle', type: 'toggle' },
            { field: 'codeReviewLifecycle', type: 'toggle' },
            { field: 'vulnTestOnUpdates', type: 'toggle' },
            { field: 'addressPromptly', type: 'likert' },
        ];
        const vulnDisclosureFields: { field: string; type: 'toggle' | 'likert' }[] = [
            { field: 'publiclyDisclose', type: 'toggle' },
            { field: 'coordinatedPolicy', type: 'toggle' },
            { field: 'contactAddress', type: 'toggle' },
            { field: 'otherMeasures', type: 'toggle' },
            { field: 'secureDistribution', type: 'toggle' },
            { field: 'patchesNoDelay', type: 'toggle' },
            { field: 'patchesFreeOfCharge', type: 'toggle' },
            { field: 'patchesWithInfo', type: 'toggle' },
        ];

        const vulnScore1 = scoreSectionFields(data.vulnManagement, vulnManagementFields);
        const vulnScore2 = scoreSectionFields(data.vulnDisclosure, vulnDisclosureFields);
        const vulnerabilities = ((vulnScore1 + vulnScore2) / 2) * 100;

        // Documentation = sbom + productDocs
        const sbomFields: { field: string; type: 'toggle' | 'likert' }[] = [
            { field: 'hasSBOM', type: 'toggle' },
            { field: 'sbomFormat', type: 'toggle' },
        ];
        const productDocsFields: { field: string; type: 'toggle' | 'likert' }[] = [
            { field: 'manufacturerDetails', type: 'toggle' },
            { field: 'vulnReportingContact', type: 'toggle' },
            { field: 'productIdentification', type: 'toggle' },
            { field: 'intendedUseDocs', type: 'toggle' },
        ];

        const docScore1 = scoreSectionFields(data.sbom, sbomFields);
        const docScore2 = scoreSectionFields(data.productDocs, productDocsFields);
        const documentation = ((docScore1 + docScore2) / 2) * 100;

        const overall = (riskAssessment + vulnerabilities + documentation) / 3;

        set({
            readinessScores: {
                riskAssessment: Math.round(riskAssessment),
                vulnerabilities: Math.round(vulnerabilities),
                documentation: Math.round(documentation),
                overall: Math.round(overall),
            },
        });
    },

    resetAssessment: () => {
        set({
            currentSubStep: 0,
            data: JSON.parse(JSON.stringify(initialData)),
            readinessScores: null,
        });
    },
}));

export default useCraReadinessStore;
