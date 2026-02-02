import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getTasks, createTask, updateTask, deleteTask, getUsers, assignUserToTask, removeUserFromTask } from '../utils/api';
import './TasksPage.css';

export default function TasksPage() {
  const { user, logout } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDescription, setNewTaskDescription] = useState('');
  const [users, setUsers] = useState([]);

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
    if (!newTaskTitle.trim()) return;

    try {
      await createTask({
        title: newTaskTitle,
        description: newTaskDescription,
        status: 'todo',
      });
      setNewTaskTitle('');
      setNewTaskDescription('');
      await loadTasks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!confirm('Are you sure you want to delete this task?')) return;

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

  if (loading) {
    return <div className="loading-state">Loading tasks...</div>;
  }

  return (
    <div className="tasks-page">
      <header className="tasks-header">
        <div className="tasks-header-content">
          <h1 className="tasks-title">Tasks</h1>
          <p className="welcome-text">Welcome back, {user?.username}! 👋</p>
        </div>
        <button onClick={logout} className="logout-btn">
          Logout
        </button>
      </header>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <section className="create-task-section">
        <h2 className="create-task-title">Create New Task</h2>
        <form onSubmit={handleCreateTask} className="create-task-form">
          <div className="form-group">
            <input
              type="text"
              placeholder="What needs to be done?"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <textarea
              placeholder="Add some details... (optional)"
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
            />
          </div>
          <button type="submit" className="submit-btn">
            Add Task
          </button>
        </form>
      </section>

      <section className="tasks-list-section">
        <div className="tasks-list-header">
          <h2>Your Tasks</h2>
          <div className="task-count-badge">{tasks.length}</div>
        </div>

        {tasks.length === 0 ? (
          <div className="empty-state">
            No tasks yet. Create your first one above!
          </div>
        ) : (
          <div className="tasks-grid">
            {tasks.map((task) => (
              <article
                key={task.id}
                className="task-card"
                data-status={task.status}
              >
                <div className="task-card-content">
                  <div className="task-card-header">
                    <div className="task-info">
                      <h3 className="task-title">{task.title}</h3>
                      {task.description && (
                        <p className="task-description">{task.description}</p>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteTask(task.id)}
                      className="delete-btn"
                      aria-label="Delete task"
                    >
                      Delete
                    </button>
                  </div>

                  <div className="status-control">
                    <label htmlFor={`status-${task.id}`} className="status-label">
                      Status
                    </label>
                    <select
                      id={`status-${task.id}`}
                      value={task.status}
                      onChange={(e) => handleStatusChange(task.id, e.target.value)}
                      className="status-select"
                    >
                      <option value="todo">To Do</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                      <option value="canceled">Canceled</option>
                    </select>
                  </div>

                  {/* User Assignment Section */}
                  <div className="assignment-control">
                    <label className="assignment-label">Assigned To</label>

                    {/* Display currently assigned users as badges */}
                    {task.assigned_to && task.assigned_to.length > 0 && (
                      <div className="assigned-users-badges">
                        {task.assigned_to.map((assignedUser) => (
                          <div key={assignedUser.id} className="user-badge">
                            <span className="user-badge-name">{assignedUser.username}</span>
                            {task.assigned_to.length > 1 && (
                              <button
                                onClick={() => handleRemoveUser(task.id, assignedUser.id)}
                                className="user-badge-remove"
                                aria-label={`Remove ${assignedUser.username}`}
                                type="button"
                              >
                                ×
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Dropdown to add users */}
                    <select
                      className="assignment-select"
                      onChange={(e) => {
                        if (e.target.value) {
                          handleAssignUser(task.id, parseInt(e.target.value));
                          e.target.value = '';
                        }
                      }}
                      defaultValue=""
                    >
                      <option value="" disabled>Add user...</option>
                      {users
                        .filter(u => !task.assigned_to?.some(au => au.id === u.id))
                        .map((user) => (
                          <option key={user.id} value={user.id}>
                            {user.username}
                          </option>
                        ))}
                    </select>
                  </div>

                  <div className="task-metadata">
                    Created {new Date(task.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
