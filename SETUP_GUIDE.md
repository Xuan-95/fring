# Fring Authentication Setup Guide

## Prerequisites

- Python 3.13+ with `uv` package manager
- Node.js and npm for the frontend
- **No database server required!** SQLite database file is created automatically

## Step 1: Backend Setup

Install dependencies:

```bash
cd backend
uv sync
```

The application uses SQLite with the database file configured in `.env.development`:
```
DATABASE_URL="sqlite:///./fring.db"
```

**The database and tables are created automatically** when you first run the application!

## Step 2: Generate Password Hashes

Create password hashes for test users:

```bash
cd backend
uv run python scripts/hash_password.py
```

You'll be prompted to enter passwords. Create passwords for two users:
- user1
- user2

The script will output bcrypt hashes. **Copy these hashes** - you'll need them in the next step.

## Step 3: Create Users

Edit `backend/scripts/create_users.sql` and replace `<hash-here>` with the hashes from Step 2:

```sql
INSERT INTO users (username, email, password_hash, is_active) VALUES
('user1', 'user1@fring.local', '$2b$12$...', true),
('user2', 'user2@fring.local', '$2b$12$...', true);
```

Then run:

```bash
sqlite3 fring.db < scripts/create_users.sql
```

Verify users were created:

```bash
sqlite3 fring.db "SELECT id, username, email, is_active FROM users;"
```

## Step 4: Start the Backend

```bash
cd backend
uv run python main.py
```

The server should start on http://localhost:8000

Check the API docs at: http://localhost:8000/docs

## Step 5: Test Authentication (Optional)

Run the Hurl test suite:

```bash
cd backend
hurl --variable host=localhost --variable port=8000 src/test/hurls/auth.hurl
```

Expected: Most tests will fail initially because user1/password123 won't match your actual credentials. Update the test file with your actual credentials if you want to run the tests.

## Step 6: Start the Frontend

In a new terminal:

```bash
cd frontend
npm install  # first time only
npm run dev
```

The app should start on http://localhost:5173

## Step 7: Test the Application

1. Visit http://localhost:5173
2. You should be redirected to the login page
3. Login with one of your created users
4. You should be redirected to the tasks page
5. Create a task - it will be automatically assigned to you
6. Logout and login as the other user
7. Verify that you only see your own tasks (task isolation works)

## Testing Shared Tasks

To test shared task functionality:

1. Login as user1
2. Create a task (it's assigned to user1)
3. Note the task ID from the browser DevTools or API response
4. Use the API directly to assign the task to user2:

```bash
# Get the access_token cookie from browser DevTools -> Application -> Cookies
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/users/{user2_id} \
  -H "Cookie: access_token=YOUR_TOKEN_HERE"
```

5. Login as user2
6. You should now see the shared task

## Troubleshooting

### "Not authenticated" errors
- Make sure cookies are being sent (check browser DevTools -> Network -> Cookies)
- Verify CORS is configured correctly in backend/main.py
- Check that frontend is accessing http://localhost:8000 (not https or different port)

### Database connection errors
- Check DATABASE_URL in backend/.env.development
- Make sure the backend directory is writable (SQLite needs to create fring.db)
- If issues persist, delete fring.db and restart the server (tables will be recreated)

### Import errors in backend
- Run `uv sync` in the backend directory
- Check that virtual environment is activated (should happen automatically with uv)

### Frontend build errors
- Run `npm install` in the frontend directory
- Clear node_modules and reinstall if needed

## Database Management

### View database contents
```bash
cd backend
sqlite3 fring.db
```

Common SQLite commands:
```sql
.tables              -- List all tables
.schema users        -- Show table structure
SELECT * FROM users; -- Query data
.quit                -- Exit
```

### Reset database
```bash
cd backend
rm fring.db
uv run python main.py  # Tables will be recreated automatically
```

## Security Notes

**Development Setup:**
- JWT secret is in .env.development (DO NOT commit to git)
- Cookies use `secure=False` for local HTTP development
- CORS allows http://localhost:5173
- SQLite database file should be in .gitignore

**For Production:**
- Generate a new JWT_SECRET_KEY (never reuse dev key)
- Set cookie `secure=True` (requires HTTPS)
- Update CORS origins to production domain
- Consider using PostgreSQL or MySQL for production (SQLite is great for development but may not handle high concurrency)
- Back up the database file regularly

## Next Steps

Optional enhancements you can add:
- Add the PasswordChange component to TasksPage
- Add user profile page showing email and account info
- Add task sharing UI (assign tasks to other users)
- Add task filtering by status
- Add pagination for tasks list
- Add user search when assigning tasks

## Why SQLite?

SQLite is perfect for development and small-scale deployments:
- **Zero configuration** - no database server to install or manage
- **Portable** - single file database that's easy to backup and version control (for schema)
- **Fast** - excellent for development and testing
- **Lightweight** - perfect for demos, prototypes, and low-traffic applications

For production applications with multiple concurrent users, consider migrating to PostgreSQL or MySQL. Thanks to SQLAlchemy, the migration is straightforward!
