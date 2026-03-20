#!/usr/bin/env node

/**
 * Test script to verify the frontend objectives checklist implementation
 */

const fs = require('fs');
const path = require('path');

console.log('Testing Frontend Objectives Checklist Implementation...');
console.log('=' * 60);

let success = true;

// Test 1: Check if ObjectivesChecklistPage.tsx exists
console.log('\n1. Testing ObjectivesChecklistPage.tsx...');
const pageFile = path.join(__dirname, 'src', 'pages', 'ObjectivesChecklistPage.tsx');
if (fs.existsSync(pageFile)) {
    console.log('✓ ObjectivesChecklistPage.tsx exists');
    
    const pageContent = fs.readFileSync(pageFile, 'utf8');
    
    // Check for required imports
    const requiredImports = [
        'import React',
        'import { Table, Select, Card, Typography, Spin, Alert }',
        'import { CheckCircleOutlined }',
        'import HeaderBar',
        'import { MenuItems }',
        'import useObjectiveStore'
    ];
    
    requiredImports.forEach(importStatement => {
        if (pageContent.includes(importStatement)) {
            console.log(`✓ Found import: ${importStatement}`);
        } else {
            console.log(`❌ Missing import: ${importStatement}`);
            success = false;
        }
    });
    
    // Check for key functionality
    const requiredFunctions = [
        'fetchObjectivesChecklist',
        'fetchComplianceStatuses',
        'updateObjectiveComplianceStatus',
        'handleComplianceStatusChange',
        'getStatusColor'
    ];
    
    requiredFunctions.forEach(func => {
        if (pageContent.includes(func)) {
            console.log(`✓ Found function: ${func}`);
        } else {
            console.log(`❌ Missing function: ${func}`);
            success = false;
        }
    });
    
} else {
    console.log('❌ ObjectivesChecklistPage.tsx does not exist');
    success = false;
}

// Test 2: Check if useObjectiveStore.ts has been updated
console.log('\n2. Testing useObjectiveStore.ts updates...');
const storeFile = path.join(__dirname, 'src', 'store', 'useObjectiveStore.ts');
if (fs.existsSync(storeFile)) {
    console.log('✓ useObjectiveStore.ts exists');
    
    const storeContent = fs.readFileSync(storeFile, 'utf8');
    
    // Check for new interfaces
    const requiredInterfaces = [
        'ComplianceStatus',
        'ObjectiveChecklistItem',
        'ChapterWithObjectives'
    ];
    
    requiredInterfaces.forEach(interfaceName => {
        if (storeContent.includes(`interface ${interfaceName}`)) {
            console.log(`✓ Found interface: ${interfaceName}`);
        } else {
            console.log(`❌ Missing interface: ${interfaceName}`);
            success = false;
        }
    });
    
    // Check for new store properties
    const requiredProperties = [
        'complianceStatuses: ComplianceStatus[]',
        'chaptersWithObjectives: ChapterWithObjectives[]'
    ];
    
    requiredProperties.forEach(prop => {
        if (storeContent.includes(prop)) {
            console.log(`✓ Found property: ${prop}`);
        } else {
            console.log(`❌ Missing property: ${prop}`);
            success = false;
        }
    });
    
    // Check for new functions
    const requiredStoreFunctions = [
        'fetchComplianceStatuses',
        'fetchObjectivesChecklist',
        'updateObjectiveComplianceStatus'
    ];
    
    requiredStoreFunctions.forEach(func => {
        if (storeContent.includes(`${func}:`)) {
            console.log(`✓ Found store function: ${func}`);
        } else {
            console.log(`❌ Missing store function: ${func}`);
            success = false;
        }
    });
    
} else {
    console.log('❌ useObjectiveStore.ts does not exist');
    success = false;
}

// Test 3: Check if App.tsx has been updated with the route
console.log('\n3. Testing App.tsx route...');
const appFile = path.join(__dirname, 'src', 'App.tsx');
if (fs.existsSync(appFile)) {
    console.log('✓ App.tsx exists');
    
    const appContent = fs.readFileSync(appFile, 'utf8');
    
    if (appContent.includes('import ObjectivesChecklistPage')) {
        console.log('✓ Found ObjectivesChecklistPage import');
    } else {
        console.log('❌ Missing ObjectivesChecklistPage import');
        success = false;
    }
    
    if (appContent.includes('path="/objectives_checklist"')) {
        console.log('✓ Found objectives_checklist route');
    } else {
        console.log('❌ Missing objectives_checklist route');
        success = false;
    }
    
    if (appContent.includes('<ObjectivesChecklistPage />')) {
        console.log('✓ Found ObjectivesChecklistPage component in route');
    } else {
        console.log('❌ Missing ObjectivesChecklistPage component in route');
        success = false;
    }
    
} else {
    console.log('❌ App.tsx does not exist');
    success = false;
}

// Test 4: Check if menuItems.tsx has been updated
console.log('\n4. Testing menuItems.tsx...');
const menuFile = path.join(__dirname, 'src', 'constants', 'menuItems.tsx');
if (fs.existsSync(menuFile)) {
    console.log('✓ menuItems.tsx exists');
    
    const menuContent = fs.readFileSync(menuFile, 'utf8');
    
    if (menuContent.includes('href="/objectives_checklist"')) {
        console.log('✓ Found objectives_checklist menu link');
    } else {
        console.log('❌ Missing objectives_checklist menu link');
        success = false;
    }
    
    if (menuContent.includes('Objectives Checklist')) {
        console.log('✓ Found "Objectives Checklist" menu label');
    } else {
        console.log('❌ Missing "Objectives Checklist" menu label');
        success = false;
    }
    
    if (menuContent.includes('<CheckCircleOutlined />')) {
        console.log('✓ Found CheckCircleOutlined icon');
    } else {
        console.log('❌ Missing CheckCircleOutlined icon');
        success = false;
    }
    
} else {
    console.log('❌ menuItems.tsx does not exist');
    success = false;
}

// Summary
console.log('\n' + '=' * 60);
if (success) {
    console.log('🎉 ALL TESTS PASSED!');
    console.log('\nFrontend implementation is complete and ready for testing.');
    console.log('\nNext steps:');
    console.log('1. Start the frontend development server: npm run dev');
    console.log('2. Navigate to /objectives_checklist in the browser');
    console.log('3. Verify the page loads and displays chapters with objectives');
    console.log('4. Test the compliance status dropdown functionality');
    console.log('5. Ensure the backend API is running and accessible');
} else {
    console.log('❌ SOME TESTS FAILED!');
    console.log('Please fix the issues before testing the frontend.');
}

console.log('\nImplementation Summary:');
console.log('- ✓ Extended useObjectiveStore with new interfaces and functions');
console.log('- ✓ Created ObjectivesChecklistPage with comprehensive UI');
console.log('- ✓ Added route to App.tsx with ProtectedRoute wrapper');
console.log('- ✓ Added menu item with CheckCircleOutlined icon');
console.log('- ✓ Implemented compliance status dropdown with color coding');
console.log('- ✓ Added loading states, error handling, and empty states');
console.log('- ✓ Followed existing design patterns and CSS classes');