import { useEffect, useState } from "react";
import { Checkbox, Tag, Button, notification, Empty, Spin } from "antd";
import { ImportOutlined } from "@ant-design/icons";
import usePolicyStore, { PolicyTemplate } from "../store/usePolicyStore";

interface PolicyTemplatesSectionProps {
    onImportComplete: () => void;
}

const PolicyTemplatesSection = ({ onImportComplete }: PolicyTemplatesSectionProps) => {
    const {
        policyTemplates,
        policies,
        fetchPolicyTemplates,
        importPolicyTemplates,
        loading,
    } = usePolicyStore();

    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [importing, setImporting] = useState(false);
    const [api, contextHolder] = notification.useNotification();

    useEffect(() => {
        fetchPolicyTemplates();
    }, [fetchPolicyTemplates]);

    // Determine which template codes are already imported
    const importedCodes = new Set(
        policies
            .map((p) => p.policy_code)
            .filter(Boolean) as string[]
    );

    // Sort templates by POL number
    const sortedTemplates = [...policyTemplates].sort((a, b) => {
        const numA = parseInt(a.policy_code?.replace("POL-", "") || "999");
        const numB = parseInt(b.policy_code?.replace("POL-", "") || "999");
        return numA - numB;
    });

    const isAlreadyImported = (template: PolicyTemplate) =>
        !!template.policy_code && importedCodes.has(template.policy_code);

    const selectableTemplates = sortedTemplates.filter((t) => !isAlreadyImported(t));

    const handleToggle = (id: string) => {
        setSelectedIds((prev) => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
    };

    const handleSelectAll = () => {
        setSelectedIds(new Set(selectableTemplates.map((t) => t.id)));
    };

    const handleDeselectAll = () => {
        setSelectedIds(new Set());
    };

    const handleImport = async () => {
        if (selectedIds.size === 0) return;
        setImporting(true);
        const result = await importPolicyTemplates(Array.from(selectedIds));
        setImporting(false);

        if (result && result.success) {
            api.success({
                message: "Import Successful",
                description: result.message,
                duration: 4,
            });
            setSelectedIds(new Set());
            onImportComplete();
        } else {
            api.error({
                message: "Import Failed",
                description: result?.message || "An error occurred while importing templates",
                duration: 4,
            });
        }
    };

    const allSelectable = selectableTemplates.length;
    const allSelected = allSelectable > 0 && selectedIds.size === allSelectable;

    if (loading && policyTemplates.length === 0) {
        return (
            <div style={{ textAlign: "center", padding: "60px 0" }}>
                <Spin size="large" />
                <p style={{ marginTop: 16, color: "var(--text-dark-gray)" }}>Loading templates...</p>
            </div>
        );
    }

    if (policyTemplates.length === 0) {
        return <Empty description="No policy templates found" />;
    }

    return (
        <div>
            {contextHolder}
            {/* Header with Select All / Deselect All and Import button */}
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 16,
                    flexWrap: "wrap",
                    gap: 12,
                }}
            >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <Button size="small" onClick={allSelected ? handleDeselectAll : handleSelectAll}>
                        {allSelected ? "Deselect All" : "Select All"}
                    </Button>
                    <span style={{ color: "var(--text-dark-gray)", fontSize: 13 }}>
                        {selectedIds.size} of {allSelectable} selectable template(s) selected
                        {importedCodes.size > 0 && (
                            <> &middot; {sortedTemplates.filter(isAlreadyImported).length} already imported</>
                        )}
                    </span>
                </div>
                <Button
                    type="primary"
                    icon={<ImportOutlined />}
                    onClick={handleImport}
                    loading={importing}
                    disabled={selectedIds.size === 0}
                >
                    Import Selected ({selectedIds.size})
                </Button>
            </div>

            {/* Template list */}
            <div
                style={{
                    border: "1px solid var(--border-light-gray)",
                    borderRadius: 8,
                    overflow: "hidden",
                }}
            >
                {sortedTemplates.map((template, index) => {
                    const alreadyImported = isAlreadyImported(template);
                    return (
                        <div
                            key={template.id}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 12,
                                padding: "10px 16px",
                                borderBottom: index < sortedTemplates.length - 1 ? "1px solid var(--border-light-gray)" : "none",
                                backgroundColor: alreadyImported
                                    ? "var(--background-off-white)"
                                    : selectedIds.has(template.id)
                                    ? "var(--primary-blue-light)"
                                    : "var(--background-white)",
                                cursor: alreadyImported ? "default" : "pointer",
                                opacity: alreadyImported ? 0.65 : 1,
                                color: "var(--text-charcoal)",
                            }}
                            onClick={() => {
                                if (!alreadyImported) handleToggle(template.id);
                            }}
                        >
                            <Checkbox
                                checked={alreadyImported || selectedIds.has(template.id)}
                                disabled={alreadyImported}
                                onChange={() => {
                                    if (!alreadyImported) handleToggle(template.id);
                                }}
                            />
                            <Tag
                                color={alreadyImported ? "default" : "blue"}
                                style={{ minWidth: 60, textAlign: "center", fontWeight: 500 }}
                            >
                                {template.policy_code || "—"}
                            </Tag>
                            <span style={{ flex: 1, fontSize: 14, color: "var(--text-charcoal)" }}>
                                {template.title || template.filename.replace(".docx", "")}
                            </span>
                            {template.file_size && (
                                <span style={{ color: "var(--text-medium-gray)", fontSize: 12 }}>
                                    {(template.file_size / 1024).toFixed(0)} KB
                                </span>
                            )}
                            {alreadyImported && (
                                <Tag color="green">Already Imported</Tag>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default PolicyTemplatesSection;
