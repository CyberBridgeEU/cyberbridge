// src/utils/menuUtils.ts
import { useState, useEffect } from 'react';

export interface MenuHighlighting {
  selectedKeys: string[];
  openKeys: string[];
}

// Route to menu key mapping
const routeToMenuMapping: Record<string, MenuHighlighting> = {
  // Dashboard (standalone)
  '/home': {
    selectedKeys: ['dashboard'],
    openKeys: []
  },
  // Assessments (parent menu with children)
  '/assessments': {
    selectedKeys: ['assessments.main'],
    openKeys: ['assessments']
  },
  '/cra-scope-assessment': {
    selectedKeys: ['assessments.cra_scope'],
    openKeys: ['assessments']
  },
  '/cra-scope-report': {
    selectedKeys: ['assessments.cra_scope'],
    openKeys: ['assessments']
  },
  '/cra-readiness-assessment': {
    selectedKeys: ['assessments.cra_readiness'],
    openKeys: ['assessments']
  },
  '/cra-readiness-report': {
    selectedKeys: ['assessments.cra_readiness'],
    openKeys: ['assessments']
  },
  // Frameworks submenu
  '/framework_management': {
    selectedKeys: ['frameworks.management'],
    openKeys: ['frameworks', 'frameworks.config']
  },
  '/chapters_objectives': {
    selectedKeys: ['frameworks.chapters'],
    openKeys: ['frameworks', 'frameworks.config']
  },
  '/framework_questions': {
    selectedKeys: ['frameworks.questions'],
    openKeys: ['frameworks', 'frameworks.config']
  },
  '/framework_updates': {
    selectedKeys: ['frameworks.updates'],
    openKeys: ['frameworks', 'frameworks.config']
  },
  '/compliance_advisor': {
    selectedKeys: ['frameworks.compliance_advisor'],
    openKeys: ['frameworks']
  },
  '/objectives_checklist': {
    selectedKeys: ['frameworks.objectives'],
    openKeys: ['frameworks']
  },
  // Assets submenu
  '/assets': {
    selectedKeys: ['assets.management'],
    openKeys: ['assets']
  },
  // Risks submenu
  '/risk_registration': {
    selectedKeys: ['risks.register'],
    openKeys: ['risks']
  },
  // Incidents submenu
  '/incidents': {
    selectedKeys: ['risks.incidents'],
    openKeys: ['risks']
  },
  // Controls submenu
  '/control_registration': {
    selectedKeys: ['controls.register'],
    openKeys: ['controls']
  },
  '/controls_library': {
    selectedKeys: ['controls.library'],
    openKeys: ['controls']
  },
  // Documents submenu
  '/policies_registration': {
    selectedKeys: ['documents.policies'],
    openKeys: ['documents']
  },
  '/architecture': {
    selectedKeys: ['documents.architecture'],
    openKeys: ['documents']
  },
  '/evidence': {
    selectedKeys: ['documents.evidence'],
    openKeys: ['documents']
  },
  '/eu_declaration_of_conformity': {
    selectedKeys: ['documents.eu_doc'],
    openKeys: ['documents']
  },
  // Compliance Chain submenu
  '/compliance_chain_links': {
    selectedKeys: ['compliance-chain.links'],
    openKeys: ['compliance-chain']
  },
  '/compliance_chain_map': {
    selectedKeys: ['compliance-chain.map'],
    openKeys: ['compliance-chain']
  },
  '/gap_analysis': {
    selectedKeys: ['compliance-chain.gap-analysis'],
    openKeys: ['compliance-chain']
  },
  // Monitoring submenu
  '/security_scanners': {
    selectedKeys: ['monitoring.security_scanners'],
    openKeys: ['monitoring']
  },
  '/code_analysis': {
    selectedKeys: ['monitoring.code_analysis'],
    openKeys: ['monitoring']
  },
  '/dependency_check': {
    selectedKeys: ['monitoring.dependency_check'],
    openKeys: ['monitoring']
  },
  '/sbom_generator': {
    selectedKeys: ['monitoring.sbom'],
    openKeys: ['monitoring']
  },
  '/scan_findings': {
    selectedKeys: ['monitoring.scan_findings'],
    openKeys: ['monitoring']
  },
  // Administration submenu
  '/history': {
    selectedKeys: ['admin.history'],
    openKeys: ['admin']
  },
  '/settings': {
    selectedKeys: ['admin.config'],
    openKeys: ['admin']
  },
  '/correlations': {
    selectedKeys: ['admin.correlations'],
    openKeys: ['admin']
  },
  '/user_management': {
    selectedKeys: ['admin.organizations'],
    openKeys: ['admin']
  },
  '/organizations': {
    selectedKeys: ['admin.organizations'],
    openKeys: ['admin']
  },
  '/users': {
    selectedKeys: ['admin.users'],
    openKeys: ['admin']
  },
  // Documentation (handled separately in sidebar)
  '/documentation': {
    selectedKeys: ['documentation'],
    openKeys: []
  },
  // Update Password
  '/update_password': {
    selectedKeys: [],
    openKeys: []
  },
  // Audit Engagements (standalone)
  '/audit-engagements': {
    selectedKeys: ['audit-engagements'],
    openKeys: []
  },
  // Background Jobs
  '/background-jobs': {
    selectedKeys: ['admin.background-jobs'],
    openKeys: ['admin']
  },
  // Dark Web Intelligence
  '/dark-web/dashboard': {
    selectedKeys: ['dark-web.dashboard'],
    openKeys: ['dark-web']
  },
  '/dark-web/scans': {
    selectedKeys: ['dark-web.scans'],
    openKeys: ['dark-web']
  },
  '/dark-web/reports': {
    selectedKeys: ['dark-web.reports'],
    openKeys: ['dark-web']
  },
  '/dark-web/settings': {
    selectedKeys: ['dark-web.settings'],
    openKeys: ['dark-web']
  }
};

/**
 * Get menu highlighting configuration for a given route
 * @param pathname - Current route pathname
 * @returns MenuHighlighting configuration with selectedKeys and openKeys
 */
export const getMenuHighlighting = (pathname: string): MenuHighlighting => {
  // Remove leading slash if present and normalize
  const normalizedPath = pathname.startsWith('/') ? pathname : `/${pathname}`;

  // Get the mapping or check for prefix-based matching (e.g., /dark-web/scan/:id)
  if (routeToMenuMapping[normalizedPath]) {
    return routeToMenuMapping[normalizedPath];
  }

  // Dynamic route matching for scan detail pages
  if (normalizedPath.startsWith('/dark-web/scan/')) {
    return { selectedKeys: ['dark-web.scans'], openKeys: ['dark-web'] };
  }

  return {
    selectedKeys: ['dashboard'], // Default to Dashboard
    openKeys: []
  };
};

/**
 * Hook to manage menu highlighting and state for current route
 * @param location - Current location from wouter useLocation hook
 * @returns MenuHighlighting configuration with state management
 */
export const useMenuHighlighting = (location: string) => {
  const routeHighlighting = getMenuHighlighting(location);
  const [openKeys, setOpenKeys] = useState<string[]>(routeHighlighting.openKeys);

  // Update openKeys when route changes and requires different parent menus to be open
  useEffect(() => {
    const newOpenKeys = routeHighlighting.openKeys;
    setOpenKeys(prevKeys => {
      // Merge current open keys with required open keys for the route
      const mergedKeys = [...new Set([...prevKeys, ...newOpenKeys])];
      return mergedKeys;
    });
  }, [location]);

  const handleOpenChange = (keys: string[]) => {
    setOpenKeys(keys);
  };

  return {
    selectedKeys: routeHighlighting.selectedKeys,
    openKeys,
    onOpenChange: handleOpenChange
  };
};