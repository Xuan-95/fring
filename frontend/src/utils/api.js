const BASE_URL = 'http://localhost:8000/api/v1';

async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const token = localStorage.getItem('access_token');

  const config = {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
  };

  try {
    let response = await fetch(url, config);

    if (response.status === 401) {
      const refreshed = await refreshToken();
      if (refreshed) {
        // Riprova la richiesta con il nuovo token
        const newToken = localStorage.getItem('access_token');
        config.headers['Authorization'] = `Bearer ${newToken}`;
        response = await fetch(url, config);
      } else {
        // Pulisci localStorage e lascia che React Router gestisca il redirect
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        throw new Error('Session expired. Please login again.');
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

async function refreshToken() {
  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function getTasks(params = {}) {
  const queryString = new URLSearchParams(params).toString();
  const endpoint = `/tasks/${queryString ? `?${queryString}` : ''}`;
  return apiRequest(endpoint);
}

export async function getTask(taskId) {
  return apiRequest(`/tasks/${taskId}`);
}

export async function createTask(taskData) {
  return apiRequest('/tasks/', {
    method: 'POST',
    body: JSON.stringify(taskData),
  });
}

export async function updateTask(taskId, taskData) {
  return apiRequest(`/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify(taskData),
  });
}

export async function deleteTask(taskId) {
  return apiRequest(`/tasks/${taskId}`, {
    method: 'DELETE',
  });
}

export async function updateTaskStatus(taskId, status) {
  return apiRequest(`/tasks/${taskId}/status?status=${status}`, {
    method: 'PATCH',
  });
}

export async function assignUserToTask(taskId, userId) {
  return apiRequest(`/tasks/${taskId}/users/${userId}`, {
    method: 'POST',
  });
}

export async function removeUserFromTask(taskId, userId) {
  return apiRequest(`/tasks/${taskId}/users/${userId}`, {
    method: 'DELETE',
  });
}
