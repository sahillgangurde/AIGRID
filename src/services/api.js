/**
 * FRAME Client API Service Layer
 * Typed helper functions connecting existing UI components to the persistent backend.
 */

const BASE_URL = ''; // Relative path leverages Vite /api proxy

function getAuthHeader() {
  const token = localStorage.getItem('frame_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function request(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...(options.headers || {})
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {}
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Authentication
  auth: {
    signup: async (data) => {
      const res = await request('/api/auth/signup', { method: 'POST', body: JSON.stringify(data) });
      if (res.access_token) {
        localStorage.setItem('frame_token', res.access_token);
        localStorage.setItem('frame_user', JSON.stringify(res.user));
      }
      return res;
    },
    login: async (credentials) => {
      const res = await request('/api/auth/login', { method: 'POST', body: JSON.stringify(credentials) });
      if (res.access_token) {
        localStorage.setItem('frame_token', res.access_token);
        localStorage.setItem('frame_user', JSON.stringify(res.user));
      }
      return res;
    },
    getMe: () => request('/api/auth/me'),
    updateProfile: (data) => request('/api/auth/profile', { method: 'PUT', body: JSON.stringify(data) }),
    logout: () => {
      localStorage.removeItem('frame_token');
      localStorage.removeItem('frame_user');
    },
    getCurrentUser: () => {
      try {
        return JSON.parse(localStorage.getItem('frame_user') || 'null');
      } catch {
        return null;
      }
    }
  },

  // Creators & Profiles
  creators: {
    list: () => request('/api/creators'),
    get: (id) => request(`/api/creators/${id}`),
    search: (filters) => request('/api/creators/search', { method: 'POST', body: JSON.stringify(filters) }),
    getTrustScore: (id) => request(`/api/creators/${id}/trust-score`),
    getAchievements: (id) => request(`/api/creators/${id}/achievements`)
  },

  // Briefs & Matching
  briefs: {
    list: () => request('/api/briefs'),
    get: (id) => request(`/api/briefs/${id}`),
    create: (data) => request('/api/briefs', { method: 'POST', body: JSON.stringify(data) }),
    aiGenerate: (data) => request('/api/briefs/ai-generate', { method: 'POST', body: JSON.stringify(data) }),
    matchCreators: (briefId) => request(`/api/briefs/${briefId}/match`)
  },

  // Feed & Social
  feed: {
    getRanked: (category = null) => request(`/api/feed${category ? `?category=${encodeURIComponent(category)}` : ''}`),
    likePost: (postId) => request(`/api/feed/${postId}/like`, { method: 'POST' }),
    savePost: (postId) => request(`/api/feed/${postId}/save`, { method: 'POST' }),
    followCreator: (creatorId) => request(`/api/feed/follow/${creatorId}`, { method: 'POST' })
  },

  // Projects & Milestones
  projects: {
    list: () => request('/api/projects'),
    get: (id) => request(`/api/projects/${id}`),
    create: (data) => request('/api/projects', { method: 'POST', body: JSON.stringify(data) }),
    updateStatus: (id, status) => request(`/api/projects/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
    updateMilestone: (projectId, milestoneId, status) => 
      request(`/api/projects/${projectId}/milestones/${milestoneId}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
    submitDraft: (projectId, data) =>
      request(`/api/projects/${projectId}/drafts`, { method: 'POST', body: JSON.stringify(data) }),
    listDrafts: (projectId) =>
      request(`/api/projects/${projectId}/drafts`)
  },

  // Messaging
  messaging: {
    listConversations: () => request('/api/conversations'),
    getMessages: (conversationId) => request(`/api/conversations/${conversationId}/messages`),
    sendMessage: (conversationId, body, attachmentRef = null) => 
      request(`/api/conversations/${conversationId}/messages`, { 
        method: 'POST', 
        body: JSON.stringify({ body, attachment_reference: attachmentRef }) 
      })
  },

  // Portfolio Publication Approvals
  approvals: {
    request: (data) => request('/api/approvals/request', { method: 'POST', body: JSON.stringify(data) }),
    review: (requestId, decision, notes = null) => 
      request(`/api/approvals/${requestId}/review`, { 
        method: 'POST', 
        body: JSON.stringify({ decision, decision_notes: notes }) 
      }),
    publish: (requestId, portfolioData) => 
      request(`/api/approvals/${requestId}/publish`, { method: 'POST', body: JSON.stringify(portfolioData) }),
    revoke: (requestId) => request(`/api/approvals/${requestId}/revoke`, { method: 'POST' })
  },

  // Collaborations
  collaborations: {
    list: () => request('/api/collaborations'),
    invite: (data) => request('/api/collaborations/invite', { method: 'POST', body: JSON.stringify(data) }),
    respond: (collabId, response) => 
      request(`/api/collaborations/${collabId}/respond`, { method: 'POST', body: JSON.stringify({ response }) }),
    complete: (collabId) => request(`/api/collaborations/${collabId}/complete`, { method: 'POST' })
  },

  // Financial Records
  finance: {
    transactions: () => request('/api/finance/transactions'),
    earnings: () => request('/api/finance/earnings'),
    demoCheckout: (creatorId, amount, currency = 'INR', projectId = null) => 
      request('/api/finance/demo-checkout', { 
        method: 'POST', 
        body: JSON.stringify({ creator_id: creatorId, gross_amount: amount, currency, project_id: projectId }) 
      })
  },

  // Customer Enquiries (Synced with Supabase enquiries table)
  enquiries: {
    list: () => request('/api/enquiries'),
    create: (data) => request('/api/enquiries', { method: 'POST', body: JSON.stringify(data) })
  },

  // Compute-Aware Escrow & Milestone Machine
  escrow: {
    calculate: (data) => request('/api/escrow/calculate', { method: 'POST', body: JSON.stringify(data) }),
    createContract: (data) => request('/api/escrow/create-contract', { method: 'POST', body: JSON.stringify(data) }),
    advanceStage: (contractId, stage) => 
      request('/api/escrow/advance-stage', { method: 'POST', body: JSON.stringify({ contract_id: contractId, stage }) }),
    getContract: (contractId) => request(`/api/escrow/contract/${contractId}`)
  },

  // Disputes & AI Fact-Finding Mediation
  disputes: {
    file: (data) => request('/api/v2/disputes/', { method: 'POST', body: JSON.stringify(data) }),
    getAiAudit: (disputeId) => request(`/api/v2/disputes/${disputeId}/ai-audit`),
    runAiAudit: (disputeId) => request(`/api/v2/disputes/${disputeId}/ai-audit`, { method: 'POST' })
  },

  // Administration & Moderation
  admin: {
    submitReport: (data) => request('/api/admin/reports', { method: 'POST', body: JSON.stringify(data) }),
    listReports: () => request('/api/admin/reports'),
    resolveReport: (reportId, status, actionTaken = null) => 
      request(`/api/admin/reports/${reportId}`, { method: 'PATCH', body: JSON.stringify({ status, action_taken: actionTaken }) }),
    getAuditLogs: () => request('/api/admin/audit-logs'),
    verifyCreator: (userId, status, isDemo = false) => 
      request('/api/admin/verify-creator', { method: 'POST', body: JSON.stringify({ user_id: userId, status, is_demo: isDemo }) })
  }
};

export default api;
