// Application constants
export const AUTH_TOKEN_KEY = 'authToken';
export const USER_DATA_KEY = 'userData';
// VITE_API_URL preferred (local or production), fallback to VITE_API_BASE_URL, then localhost.
export const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const API_TIMEOUT = 30000; // Increased to 30 seconds for cold starts
