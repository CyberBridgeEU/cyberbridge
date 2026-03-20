import { create } from 'zustand';

export interface CompanyDetails {
    companyName: string;
    contactName: string;
    companySize: string;
    productName: string;
}

export interface ProductDetails {
    isDigitalProduct: boolean;
    connectsToNetwork: boolean;
    isSaaS: boolean;
}

export interface MarketInfo {
    euMarket: boolean;
    compliesWithRegulations: boolean;
    operatorRole: string;
}

type ScopeResult = 'IN_SCOPE' | 'OUT_OF_SCOPE' | null;

interface CraScopeStore {
    currentStep: number;
    companyDetails: CompanyDetails;
    productDetails: ProductDetails;
    marketInfo: MarketInfo;
    scopeResult: ScopeResult;

    nextStep: () => void;
    prevStep: () => void;
    setCompanyField: <K extends keyof CompanyDetails>(field: K, value: CompanyDetails[K]) => void;
    setProductField: <K extends keyof ProductDetails>(field: K, value: ProductDetails[K]) => void;
    setMarketField: <K extends keyof MarketInfo>(field: K, value: MarketInfo[K]) => void;
    calculateScope: () => void;
    resetAssessment: () => void;
}

const useCraScopeStore = create<CraScopeStore>((set, get) => ({
    currentStep: 0,
    companyDetails: {
        companyName: '',
        contactName: '',
        companySize: '',
        productName: '',
    },
    productDetails: {
        isDigitalProduct: false,
        connectsToNetwork: false,
        isSaaS: false,
    },
    marketInfo: {
        euMarket: false,
        compliesWithRegulations: false,
        operatorRole: '',
    },
    scopeResult: null,

    nextStep: () => {
        const { currentStep } = get();
        set({ currentStep: Math.min(currentStep + 1, 3) });
    },

    prevStep: () => {
        const { currentStep } = get();
        set({ currentStep: Math.max(currentStep - 1, 0) });
    },

    setCompanyField: (field, value) => {
        const { companyDetails } = get();
        set({ companyDetails: { ...companyDetails, [field]: value } });
    },

    setProductField: (field, value) => {
        const { productDetails } = get();
        set({ productDetails: { ...productDetails, [field]: value } });
    },

    setMarketField: (field, value) => {
        const { marketInfo } = get();
        set({ marketInfo: { ...marketInfo, [field]: value } });
    },

    calculateScope: () => {
        const { marketInfo, productDetails } = get();

        // NOT on EU market → OUT_OF_SCOPE
        if (!marketInfo.euMarket) {
            set({ scopeResult: 'OUT_OF_SCOPE' });
            return;
        }

        // Complies with listed EU regulations → OUT_OF_SCOPE
        if (marketInfo.compliesWithRegulations) {
            set({ scopeResult: 'OUT_OF_SCOPE' });
            return;
        }

        // Not a digital product → OUT_OF_SCOPE
        if (!productDetails.isDigitalProduct) {
            set({ scopeResult: 'OUT_OF_SCOPE' });
            return;
        }

        // Otherwise → IN_SCOPE
        set({ scopeResult: 'IN_SCOPE' });
    },

    resetAssessment: () => {
        set({
            currentStep: 0,
            companyDetails: {
                companyName: '',
                contactName: '',
                companySize: '',
                productName: '',
            },
            productDetails: {
                isDigitalProduct: false,
                connectsToNetwork: false,
                isSaaS: false,
            },
            marketInfo: {
                euMarket: false,
                compliesWithRegulations: false,
                operatorRole: '',
            },
            scopeResult: null,
        });
    },
}));

export default useCraScopeStore;
