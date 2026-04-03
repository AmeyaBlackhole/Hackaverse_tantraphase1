import axios from 'axios';
import { API_BASE_URL, API_TIMEOUT } from '../constants/appConstants';

// Create axios instance with default config
const api = (axios.create || (() => axios))({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token and API key
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Add API key from env
    const apiKey = import.meta.env.VITE_API_KEY || '2b899caf7e3aea924c96761326bdded5162da31a9d1fdba59a2a451d2335c778';
    config.headers['X-API-Key'] = apiKey;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('userData');
      window.location.href = '/';
    } else if (error.response) {
      // Handle different HTTP error statuses
      const status = error.response.status;
      let errorMessage = 'An error occurred';

      if (status === 400) {
        errorMessage = 'Bad request: ' + (error.response.data?.message || 'Invalid data');
      } else if (status === 403) {
        errorMessage = 'Forbidden: You do not have permission to access this resource';
      } else if (status === 404) {
        errorMessage = 'Resource not found';
      } else if (status === 500) {
        errorMessage = 'Server error: Please try again later';
      } else if (status >= 500) {
        errorMessage = 'Server unavailable: Please try again later';
      }

      // Add the error message to the error object for better handling
      error.message = errorMessage;
      error.userMessage = errorMessage;
    } else if (error.request) {
      // Request was made but no response received
      error.message = 'Network error: No response from server';
      error.userMessage = 'Network error: Please check your connection';
    } else {
      // Something happened in setting up the request
      error.message = 'Request setup error: ' + error.message;
      error.userMessage = 'Request failed: Please try again';
    }

    return Promise.reject(error);
  }
);

// Validation utilities
const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(String(email).toLowerCase());
};

const validatePassword = (password) => {
  return password && password.length >= 6;
};

const validateUserData = (userData) => {
  const errors = [];

  if (!userData.email || !validateEmail(userData.email)) {
    errors.push('Valid email is required');
  }

  if (!userData.password || !validatePassword(userData.password)) {
    errors.push('Password must be at least 6 characters');
  }

  if (!userData.name || userData.name.trim().length < 2) {
    errors.push('Name must be at least 2 characters');
  }

  return errors.length > 0 ? errors : null;
};

const validateAgentData = (data) => {
  const errors = [];

  if (!data.message || data.message.trim().length === 0) {
    errors.push('Message cannot be empty');
  }

  if (data.message.length > 1000) {
    errors.push('Message is too long (max 1000 characters)');
  }

  return errors.length > 0 ? errors : null;
};

const validateRewardData = (data) => {
  const errors = [];

  if (!data.user_id || isNaN(data.user_id)) {
    errors.push('Valid user ID is required');
  }

  if (!data.achievement_type || data.achievement_type.trim().length === 0) {
    errors.push('Achievement type is required');
  }

  if (!data.points || isNaN(data.points) || data.points <= 0) {
    errors.push('Valid positive points value is required');
  }

  return errors.length > 0 ? errors : null;
};

// API Service Methods with validation
export const apiService = {
  // Authentication
  auth: {
    login: (credentials) => {
      if (!credentials.email || !credentials.password) {
        return Promise.reject(new Error('Email and password are required'));
      }
      return api.post('/auth/login', credentials);
    },
    register: (userData) => {
      const validationErrors = validateUserData(userData);
      if (validationErrors) {
        return Promise.reject(new Error(validationErrors.join(', ')));
      }
      return api.post('/auth/register', userData);
    },
    logout: () => {
      const refreshToken = localStorage.getItem('refreshToken');
      return api.post('/auth/logout', { refresh_token: refreshToken });
    },
    refreshToken: () => {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        return Promise.reject(new Error('No refresh token available'));
      }
      return api.post('/auth/refresh', { refresh_token: refreshToken });
    },
  },

  // Agent endpoints
  agent: {
    sendMessage: (data) => {
      if (!data.question || data.question.trim().length === 0) {
        return Promise.reject(new Error('Message cannot be empty'));
      }
      return api.post('/ai/agent', { question: data.question });
    },
    getHistory: (teamId) => api.get(`/agent/history/${teamId}`).catch(() => Promise.resolve({ data: [] })),
  },

  // Admin endpoints
  admin: {
    inviteJudge: (email) => api.post('/judge/invitations/send', { email, hackathon_name: 'HackaVerse' }),
    inviteParticipant: (email, hackathonId) => api.post('/admin/invite-participant', { email, hackathonId }),
    getDashboard: () => api.get('/admin/dashboard'),
    getRewards: () => api.get('/reward').catch(() => Promise.resolve({ data: [] })),
    applyReward: (data) => {
      const validationErrors = validateRewardData(data);
      if (validationErrors) {
        return Promise.reject(new Error(validationErrors.join(', ')));
      }
      return api.post('/reward', data);
    },
    getLogs: (params) => {
      if (params && (params.limit && isNaN(params.limit))) {
        return Promise.reject(new Error('Invalid limit parameter'));
      }
      return api.get('/system/logs', { params });
    },
    registerTeam: (data) => api.post('/registration', data),
    getTeams: () => api.get('/teams'),
    getProjects: () => api.get('/projects'),
    getSubmissions: () => api.get('/submissions'),
    getParticipants: () => api.get('/hackathons/{id}/participants').catch(() => Promise.resolve({ data: [] })),
  },

  // Hackathon endpoints
  hackathons: {
    getAll: () => api.get('/hackathons'),
    getActive: () => api.get('/hackathons/active'),
    create: (data) => api.post('/hackathons', data),
    update: (id, data) => api.patch(`/hackathons/${id}`, data),
    join: (data) => api.post('/hackathons/join', data),
  },

  // System endpoints
  system: {
    health: () => api.get('/system/health'),
    status: () => api.get('/system/ready'),
  },

  // Teams
  teams: {
    getAll: () => api.get('/teams'),
    getById: (id) => api.get(`/teams/${id}`),
    create: (data) => api.post('/teams', data),
    update: (id, data) => api.patch(`/teams/${id}`, data).catch(() => Promise.resolve({ data: null })),
    delete: (id) => api.delete(`/teams/${id}`).catch(() => Promise.resolve({ data: null })),
    join: (id) => api.post(`/teams/${id}/join`, {}).catch(() => Promise.resolve({ data: null })),
    leave: (id) => api.post(`/teams/${id}/leave`, {}).catch(() => Promise.resolve({ data: null })),
    sendInvitation: (data) => api.post('/teams/invitations/send', data),
    acceptInvitation: (token) => api.post('/teams/invitations/accept', { token }),
    acceptInvitationWithDetails: (data) => api.post('/teams/invitations/accept-with-details', data),
    getInvitationDetails: (token) => api.get(`/teams/invitations/${token}`),
    getReceivedInvitations: () => api.get('/teams/invitations/received'),
    getSentInvitations: () => api.get('/teams/invitations/sent'),
    respondToInvitation: (data) => api.post('/teams/invitations/respond', data),
    updateTeamMember: (data) => api.put('/teams/members/update', data),
    updateTeamDetails: (data) => api.put('/teams/update-details', data),
    getTeamDetails: (teamId) => api.get(`/teams/${teamId}/details`),
    getTeamMembers: (teamId) => api.get(`/teams/${teamId}/members`),
  },

  // Submissions
  submissions: {
    getAll: () => api.get('/submissions'),
    getById: (id) => api.get(`/submissions/${id}`),
    getByTeam: (teamId) => api.get(`/submissions/team/${teamId}`),
    create: (data) => api.post('/submissions', data),
    update: (id, data) => api.patch(`/submissions/${id}`, data).catch(() => Promise.resolve({ data: null })),
  },

  // Leaderboard
  leaderboard: {
    get: (hackathonId, params = {}) => {
      const { limit = 50 } = params;
      return api.get(`/leaderboard/${hackathonId}`, { params: { limit } });
    },
    getByTrack: (track) => Promise.resolve({ data: [] }),
  },

  // Judge endpoints
  judge: {
    scoreSubmission: (data) => {
      if (!data.submission_text || data.submission_text.trim().length === 0) {
        return Promise.reject(new Error('Submission text cannot be empty'));
      }
      const payload = {
        submission_text: data.submission_text,
        team_id: data.team_id || null,
        tenant_id: data.tenant_id || 'default',
        event_id: data.event_id || 'default_event',
        workspace_id: data.workspace_id || null
      };
      return api.post('/judge/score', payload);
    },
    submitAndScore: (data) => {
      if (!data.submission_text || data.submission_text.trim().length === 0) {
        return Promise.reject(new Error('Submission text cannot be empty'));
      }
      const payload = {
        submission_text: data.submission_text,
        team_id: data.team_id || null,
        tenant_id: data.tenant_id || 'default',
        event_id: data.event_id || 'default_event',
        workspace_id: data.workspace_id || null,
        request_id: data.request_id || null
      };
      return api.post('/judge/submit', payload);
    },
    getRubric: () => api.get('/judge/rubric'),
    batchJudge: (data) => {
      if (!data.submissions || data.submissions.length === 0) {
        return Promise.reject(new Error('At least one submission is required'));
      }
      const payload = {
        submissions: data.submissions,
        tenant_id: data.tenant_id || 'default',
        event_id: data.event_id || 'default_event',
        workspace_id: data.workspace_id || null
      };
      return api.post('/judge/batch', payload);
    },
    getRankings: (params = {}) => {
      const { tenant_id = 'default', event_id = 'default_event', limit = 50 } = params;
      return api.get('/judge/rank', { params: { tenant_id, event_id, limit } });
    },
    getPendingSubmissions: () => api.get('/judge/submissions/pending'),
    submitReview: (data) => api.post('/judge/review/submit', data),
    getScores: (projectId) => api.get(`/judging/scores/${projectId}`),
  },

  // User profile
  user: {
    getProfile: () => api.get('/user/profile').catch(() => Promise.resolve({ data: null })),
    updateProfile: (data) => api.patch('/user/profile', data).catch(() => Promise.resolve({ data: null })),
    getStats: () => api.get('/user/stats').catch(() => Promise.resolve({ data: null })),
  },

  // Notifications
  notifications: {
    getAll: (userId) => api.get(`/notifications/user/${userId}`),
    getUnread: (userId) => api.get(`/notifications/user/${userId}?unread_only=true`),
    markRead: (notificationId) => api.patch(`/notifications/read/${notificationId}`),
    markAllRead: (userId) => api.patch(`/notifications/read-all/${userId}`),
    create: (data) => api.post('/notifications/create', data),
  },

  // Announcements
  announcements: {
    getAll: () => api.get('/notifications/announcements'),
    create: (data) => api.post('/notifications/announcements', data),
  },
};

export default api;
