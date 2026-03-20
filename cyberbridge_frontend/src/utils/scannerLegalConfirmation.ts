import { useState, useCallback, useRef } from 'react';

export const useScannerLegalConfirmation = () => {
    const [visible, setVisible] = useState(false);
    const [scannerName, setScannerName] = useState('');
    const resolveRef = useRef<((value: boolean) => void) | null>(null);

    const confirmScanLegalDisclaimer = useCallback((name: string): Promise<boolean> => {
        setScannerName(name);
        setVisible(true);
        return new Promise<boolean>((resolve) => {
            resolveRef.current = resolve;
        });
    }, []);

    const handleOk = useCallback(() => {
        setVisible(false);
        resolveRef.current?.(true);
        resolveRef.current = null;
    }, []);

    const handleCancel = useCallback(() => {
        setVisible(false);
        resolveRef.current?.(false);
        resolveRef.current = null;
    }, []);

    return { visible, scannerName, handleOk, handleCancel, confirmScanLegalDisclaimer };
};
