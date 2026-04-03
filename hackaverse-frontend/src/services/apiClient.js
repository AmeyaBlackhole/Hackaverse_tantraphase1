import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '2b899caf7e3aea924c96761326bdded5162da31a9d1fdba59a2a451d2335c778';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
});

// Admin APIs
export const adminAPI = {
  getDashboard: () => apiClient.get('/api/admin/dashboard'),
  createHackathon: (data) => apiClient.post('/api/hackathons', data),
  inviteJudge: (email) => apiClient.post('/api/admin/invite-judge', { email }),
  inviteParticipant: (email, hackathonId) => 
    apiClient.post('/api/admin/invite-participant', { email, hackathonId }),
  getActivityLogs: (limit = 10) => apiClient.get(`/admin/logs?limit=${limit}`)
};

// Submission APIs
export const submissionAPI = {
  getAllSubmissions: () => apiClient.get('/submissions'),
  getSubmissionById: (submissionId) => apiClient.get(`/submissions/${submissionId}`),
  getTeamSubmissions: (teamId) => apiClient.get(`/submissions/team/${teamId}`),
  createSubmission: (data) => apiClient.post('/submissions', data),
};

// Invitation APIs
export const invitationAPI = {
  getInvitations: (userEmail) => apiClient.get(`/invitations?user_email=${userEmail}`),
  acceptInvitation: (invitationId) => apiClient.post(`/invitations/${invitationId}/accept`),
  declineInvitation: (invitationId) => apiClient.post(`/invitations/${invitationId}/decline`)
};

// Judging APIs
export const judgingAPI = {
  scoreProject: (data) => apiClient.post('/api/judging/score', data),
  getProjectScores: (projectId) => apiClient.get(`/api/judging/scores/${projectId}`)
};

// Announcements APIs
export const announcementsAPI = {
  getAll: () => apiClient.get('/notifications/announcements'),
  create: (data) => apiClient.post('/notifications/announcements', data)
};

// Leaderboard APIs
export const leaderboardAPI = {
  getLeaderboard: (hackathonId, limit = 50) => apiClient.get(`/api/hackathons/${hackathonId}/leaderboard`, { params: { limit } })
};

export default apiClient;
