import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getTasks, createTask, updateTask, deleteTask, getUsers, assignUserToTask, removeUserFromTask } from '../utils/api';
import './TasksPage.css';

export default function TasksPage() {
  const { user, logout } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [users, setUsers] = useState([]);
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    status: 'todo',
    dueDate: ''
  });

  const loadTasks = async () => {
    try {
      setLoading(true);
      const data = await getTasks();
      setTasks(data);
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await getUsers();
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users:', err);
    }
  };

  useEffect(() => {
    loadTasks();
    loadUsers();
  }, []);

  const handleCreateTask = async (e) => {
    e.preventDefault();
    if (!newTask.title.trim()) return;

    try {
      await createTask({
        title: newTask.title,
        description: newTask.description,
        status: newTask.status,
        due_date: newTask.dueDate || null
      });
      setNewTask({ title: '', description: '', status: 'todo', dueDate: '' });
      setShowQuickAdd(false);
      await loadTasks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!confirm('Delete this task?')) return;

    try {
      await deleteTask(taskId);
      await loadTasks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await updateTask(taskId, { status: newStatus });
      await loadTasks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAssignUser = async (taskId, userId) => {
    try {
      await assignUserToTask(taskId, userId);
      await loadTasks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRemoveUser = async (taskId, userId) => {
    try {
      await removeUserFromTask(taskId, userId);
      await loadTasks();
    } catch (err) {
      setError(err.message);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getStatusColor = (status) => {
    const colors = {
      todo: 'var(--status-todo)',
      in_progress: 'var(--status-progress)',
      completed: 'var(--status-done)',
      canceled: 'var(--status-canceled)'
    };
    return colors[status] || colors.todo;
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading tasks...</p>
      </div>
    );
  }

  return (
    <div className="tasks-page">
      <header className="page-header">
        <div className="header-content">
          <h1 className="page-title">Fring</h1>
          <p className="welcome-text">Welcome back, {user?.username}</p>
        </div>
        <button onClick={logout} className="logout-btn">
          Sign out
        </button>
      </header>

      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠</span>
          {error}
        </div>
      )}

      <main className="main-content">
        <div className="content-header">
          <div className="content-header-left">
            <h2>Tasks</h2>
            <span className="task-count">{tasks.length}</span>
          </div>
          <button
            onClick={() => setShowQuickAdd(!showQuickAdd)}
            className="btn-primary"
          >
            {showQuickAdd ? 'Cancel' : '+ New task'}
          </button>
        </div>

        {showQuickAdd && (
          <form onSubmit={handleCreateTask} className="quick-add-form">
            <div className="quick-add-grid">
              <input
                type="text"
                placeholder="Task title"
                value={newTask.title}
                onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                className="quick-add-input title-input"
                required
                autoFocus
              />
              <input
                type="text"
                placeholder="Description (optional)"
                value={newTask.description}
                onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                className="quick-add-input"
              />
              <input
                type="date"
                value={newTask.dueDate}
                onChange={(e) => setNewTask({ ...newTask, dueDate: e.target.value })}
                className="quick-add-input date-input"
              />
              <button type="submit" className="btn-primary btn-small">
                Create
              </button>
            </div>
          </form>
        )}

        {tasks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <h3>No tasks yet</h3>
            <p>Create your first task to get started</p>
          </div>
        ) : (
          <div className="tasks-table-container">
            <table className="tasks-table">
              <thead>
                <tr>
                  <th className="col-title">Task</th>
                  <th className="col-status">Status</th>
                  <th className="col-assigned">Assigned</th>
                  <th className="col-due">Due</th>
                  <th className="col-actions"></th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task, index) => (
                  <tr
                    key={task.id}
                    className="task-row"
                    style={{ animationDelay: `${index * 0.03}s` }}
                  >
                    <td className="task-title-cell">
                      <div className="task-title-content">
                        <span
                          className="status-indicator"
                          style={{ backgroundColor: getStatusColor(task.status) }}
                        ></span>
                        <div className="task-text">
                          <h3 className="task-title">{task.title}</h3>
                          {task.description && (
                            <p className="task-description">{task.description}</p>
                          )}
                        </div>
                      </div>
                    </td>

                    <td className="task-status-cell">
                      <select
                        value={task.status}
                        onChange={(e) => handleStatusChange(task.id, e.target.value)}
                        className="status-select"
                        style={{ color: getStatusColor(task.status) }}
                      >
                        <option value="todo">To Do</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                        <option value="canceled">Canceled</option>
                      </select>
                    </td>

                    <td className="task-assigned-cell">
                      <div className="assigned-users">
                        {task.assigned_to && task.assigned_to.length > 0 ? (
                          <div className="user-chips">
                            {task.assigned_to.map((assignedUser) => (
                              <div key={assignedUser.id} className="user-chip">
                                <span className="user-avatar">
                                  {assignedUser.username.charAt(0).toUpperCase()}
                                </span>
                                <span className="user-name">{assignedUser.username}</span>
                                {task.assigned_to.length > 1 && (
                                  <button
                                    onClick={() => handleRemoveUser(task.id, assignedUser.id)}
                                    className="user-remove"
                                    type="button"
                                    aria-label={`Remove ${assignedUser.username}`}
                                  >
                                    ×
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="unassigned-text">Unassigned</span>
                        )}
                        <select
                          className="user-select"
                          onChange={(e) => {
                            if (e.target.value) {
                              handleAssignUser(task.id, parseInt(e.target.value));
                              e.target.value = '';
                            }
                          }}
                          defaultValue=""
                        >
                          <option value="" disabled>+ Add</option>
                          {users
                            .filter(u => !task.assigned_to?.some(au => au.id === u.id))
                            .map((user) => (
                              <option key={user.id} value={user.id}>
                                {user.username}
                              </option>
                            ))}
                        </select>
                      </div>
                    </td>

                    <td className="task-due-cell">
                      <span className="due-date">
                        {formatDate(task.due_date)}
                      </span>
                    </td>

                    <td className="task-actions-cell">
                      <button
                        onClick={() => handleDeleteTask(task.id)}
                        className="btn-delete"
                        aria-label="Delete task"
                      >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <path d="M2 4h12M5.333 4V2.667a1.333 1.333 0 0 1 1.334-1.334h2.666a1.333 1.333 0 0 1 1.334 1.334V4m2 0v9.333a1.333 1.333 0 0 1-1.334 1.334H4.667a1.333 1.333 0 0 1-1.334-1.334V4h9.334Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
