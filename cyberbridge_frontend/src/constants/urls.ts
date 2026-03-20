// URL constants for API endpoints

// Environment detection
const isProduction = import.meta.env.PROD;
const isDevelopment = import.meta.env.DEV;

// Detect if we're accessing from localhost or remotely
const isLocalhost = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

// Get the current host for development when accessed remotely
const getDevBaseUrl = () => {
  if (typeof window !== 'undefined' && !isLocalhost) {
    // Use the same host the browser is connected to
    return `http://${window.location.hostname}`;
  }
  return 'http://localhost';
};

// Base configuration
const config = {
  development: {
    baseUrl: getDevBaseUrl(),
    ports: {
      backend: 8000,
      zap: 8010,
      nmap: 8011,
      osv: 8012,
      semgrep: 8013,
      syft: 8014,
    }
  },
  production: {
    // Use environment variable if available, otherwise fallback to default IP
    baseUrl: import.meta.env.VITE_PRODUCTION_IP || 'https://api.cyberbridge.eu',
    zapUrl: 'https://zap.cyberbridge.eu',  // ZAP via HTTPS subdomain
    ports: {
      backend: import.meta.env.VITE_BACKEND_PORT || '',  // Set for local dev, empty for reverse proxy
      zap: 8010,
      nmap: 8011,
      osv: 8012,
      semgrep: 8013,
      syft: 8014
    }
  }
};

// Get current environment config
const currentConfig = isProduction ? config.production : config.development;

// Backend REST API URL - handle port conditionally
export const cyberbridge_back_end_rest_api = currentConfig.ports.backend
  ? `${currentConfig.baseUrl}:${currentConfig.ports.backend}`
  : currentConfig.baseUrl;

// ZAP REST API wrapper URL - use subdomain in production, port in development
export const zap_rest_api_wrapper = isProduction && config.production.zapUrl
  ? config.production.zapUrl
  : `${currentConfig.baseUrl}:${currentConfig.ports.zap}`;

// Nmap REST API wrapper URL
export const nmap_rest_api_wrapper = `${currentConfig.baseUrl}:${currentConfig.ports.nmap}`;

// Semgrep REST API wrapper URL
export const semgrep_rest_api_wrapper = `${currentConfig.baseUrl}:${currentConfig.ports.semgrep}`;

// OSV REST API wrapper URL
export const osv_rest_api_wrapper = `${currentConfig.baseUrl}:${currentConfig.ports.osv}`;

// Syft SBOM REST API wrapper URL
export const syft_rest_api_wrapper = `${currentConfig.baseUrl}:${currentConfig.ports.syft}`;

// CTI Dashboard API (proxied through CyberBridge backend)
export const cti_rest_api = `${cyberbridge_back_end_rest_api}/cti`;

// Dark Web Scanner API (proxied through CyberBridge backend at /dark-web/*)
export const dark_web_rest_api = `${cyberbridge_back_end_rest_api}/dark-web`;

