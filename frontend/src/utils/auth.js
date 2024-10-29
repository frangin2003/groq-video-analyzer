// Create a new utility file for auth-related functions
export const getAuthHeaders = () => {
  // Check if we're in local development
  const isLocal = process.env.REACT_APP_LOCAL === 'true';
  
  if (isLocal) {
    return {
      'Accept': 'application/json'
    };
  }

  const token = localStorage.getItem('auth_token');
  return {
    'Accept': 'application/json',
    'Authorization': `Bearer ${token}`
  };
};

export const getWebSocketUrl = (taskId) => {
  const isLocal = process.env.REACT_APP_LOCAL === 'true';
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const baseUrl = `${wsProtocol}//${window.location.host}/api/ws/${taskId}`;
  
  if (isLocal) {
    return baseUrl;
  }

  const token = localStorage.getItem('auth_token');
  return `${baseUrl}?token=${token}`;
}; 