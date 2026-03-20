import { useMemo } from 'react';
import useCRAModeStore from '../store/useCRAModeStore';
import useFrameworksStore from '../store/useFrameworksStore';

interface HasIdAndName {
    id: string;
    name: string;
}

/**
 * Filters frameworks to only show the CRA framework when CRA mode is 'focused'.
 * Accepts an optional override list (e.g. from usePolicyStore) — otherwise
 * reads from useFrameworksStore.
 */
function useCRAFilteredFrameworks<T extends HasIdAndName>(overrideFrameworks?: T[]) {
    const craMode = useCRAModeStore((s) => s.craMode);
    const storeFrameworks = useFrameworksStore((s) => s.frameworks);

    const frameworks = (overrideFrameworks ?? storeFrameworks) as T[];

    const craFramework = useMemo(
        () => frameworks.find((f) => f.name.toLowerCase() === 'cra') ?? null,
        [frameworks],
    );

    const filteredFrameworks = useMemo(() => {
        if (craMode === 'focused' && craFramework) return [craFramework];
        return frameworks;
    }, [craMode, craFramework, frameworks]);

    return {
        filteredFrameworks,
        craFrameworkId: craFramework?.id ?? null,
        isCRAModeActive: craMode !== null && craFramework !== null,
        isCRAFocused: craMode === 'focused' && craFramework !== null,
        isCRAExtended: craMode === 'extended' && craFramework !== null,
    };
}

export default useCRAFilteredFrameworks;
