// src/data/frameworksData.ts

export interface Framework {
    name: string;
    description: string;
}

export const frameworks: Framework[] = [
    { name: "ISO 27001", description: "Information Security Management System Standard" },
    { name: "GDPR", description: "General Data Protection Regulation" },
    { name: "HIPAA", description: "Health Insurance Portability and Accountability Act" },
    { name: "PCI DSS", description: "Payment Card Industry Data Security Standard" },
    { name: "SOC 2", description: "Service Organization Control 2" },
    { name: "NIST CSF", description: "National Institute of Standards and Technology Cybersecurity Framework" }
];
