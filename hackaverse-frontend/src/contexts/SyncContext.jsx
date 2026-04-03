import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const SyncContext = createContext();

export const useSyncContext = () => {
  const context = useContext(SyncContext);
  if (!context) {
    throw new Error('useSyncContext must be used within SyncProvider');
  }
  return context;
};

export const SyncProvider = ({ children }) => {
  const [syncData, setSyncData] = useState({
    teams: [],
    participants: [],
    hackathons: [],
    projects: [],
    submissions: [],
    activities: [],
    events: [],
    lastUpdate: null
  });

  const fetchAllData = useCallback(async () => {
    try {
      const apiKey = import.meta.env.VITE_API_KEY || '2b899caf7e3aea924c96761326bdded5162da31a9d1fdba59a2a451d2335c778';
      const baseUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const authToken = localStorage.getItem('authToken');
      const headers = {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {})
      };

      const [teamsRes, hackathonsRes, submissionsRes, activitiesRes] = await Promise.all([
        fetch(`${baseUrl}/teams/list`, { headers }).catch(() => null),
        fetch(`${baseUrl}/api/hackathons`, { headers }).catch(() => null),
        fetch(`${baseUrl}/submissions`, { headers }).catch(() => null),
        fetch(`${baseUrl}/api/admin/dashboard`, { headers }).catch(() => null)
      ]);

      const teams = teamsRes ? (await teamsRes.json()).data || [] : [];
      const hackathons = hackathonsRes ? (await hackathonsRes.json()).data || [] : [];
      const submissions = submissionsRes ? (await submissionsRes.json()).data || [] : [];
      const dashboardData = activitiesRes ? (await activitiesRes.json()).data || {} : {};
      const activities = dashboardData.recentActivities || [];

      const participantsMap = new Map();
      teams.forEach(team => {
        const members = team.members || [];
        members.forEach(member => {
          const memberId = typeof member === 'object' ? member.user_id : member;
          if (memberId && !participantsMap.has(memberId)) {
            participantsMap.set(memberId, {
              id: memberId,
              name: typeof member === 'object' ? member.name : `User ${memberId}`,
              email: typeof member === 'object' ? member.email : `user${memberId}@hackaverse.com`
            });
          }
        });
      });

      setSyncData({
        teams,
        hackathons,
        submissions,
        activities,
        events: activities,
        participants: Array.from(participantsMap.values()),
        lastUpdate: new Date().toISOString()
      });
    } catch (error) {
      console.error('Sync error:', error);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 10000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const value = {
    syncData,
    teams: syncData.teams,
    hackathons: syncData.hackathons,
    submissions: syncData.submissions,
    activities: syncData.activities,
    events: syncData.events,
    participants: syncData.participants
  };

  return (
    <SyncContext.Provider value={value}>
      {children}
    </SyncContext.Provider>
  );
};
