// Simple test to verify the PDF export functionality
const testProducts = [
    {
        id: "1",
        product_name: "Test Product 1",
        product_version: "1.0.0",
        justification: "This is a test product for demonstration purposes",
        license_model: "MIT License",
        description: "A comprehensive test product that demonstrates all the features of our PDF export functionality",
        sbom: '{"name": "test-product", "version": "1.0.0", "supplier": {"name": "Test Company"}, "components": [{"name": "component1", "version": "1.0"}, {"name": "component2", "version": "2.0"}]}',
        product_status: "Live",
        economic_operator: "Manufacturer",
        product_type: "Software",
        criticality: "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I - Identity management systems"
    },
    {
        id: "2",
        product_name: "Test Product 2",
        product_version: "2.1.0",
        justification: "Another test product with plain text SBOM",
        license_model: "Apache 2.0",
        description: "This product has a plain text SBOM to test different formatting",
        sbom: "This is a plain text SBOM with component information:\n- Component A v1.0\n- Component B v2.0\n- Component C v1.5",
        product_status: "Testing",
        economic_operator: "Distributor",
        product_type: "Hardware",
        criticality: "ANNEX IV - CRITICAL PRODUCTS WITH DIGITAL ELEMENTS - Hardware Devices with Security Boxes"
    }
];

console.log("Test data prepared for PDF export:");
console.log("Number of products:", testProducts.length);
console.log("Products:", testProducts.map(p => `${p.product_name} v${p.product_version}`));
console.log("\nTo test the PDF export:");
console.log("1. Start the frontend application");
console.log("2. Navigate to the Products page");
console.log("3. Click the 'Export to PDF' button");
console.log("4. Verify the PDF contains properly formatted product information");
console.log("5. Check that JSON SBOM is parsed and displayed correctly");
console.log("6. Verify that plain text SBOM is displayed as-is");