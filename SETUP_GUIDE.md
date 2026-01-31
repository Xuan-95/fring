# Fring Authentication Setup Guide

## Prerequisites

Make sure PostgreSQL is running and you have the database created:
```bash
createdb life-manager  # or your preferred database name
```

## Step 1: Run Database Migration

Add the authentication fields to the users table:

```bash
cd backend
psql postgresql://postgres:postgres@localhost/life-manager -f migrations/001_add_auth_fields.sql
```

Expected output:
```
ALTER TABLE
```

## Step 2: Generate Password Hashes

Run the password hashing script:

```bash
cd backend
python scripts/hash_password.py
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
psql postgresql://postgres:postgres@localhost/life-manager -f scripts/create_users.sql
```

Verify users were created:

```bash
psql postgresql://postgres:postgres@localhost/life-manager -c "SELECT id, username, email, is_active FROM users;"
```

## Step 4: Start the Backend

```bash
cd backend
python main.py
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
- Verify PostgreSQL is running
- Check DATABASE_URL in backend/.env.development
- Make sure the database exists

### Import errors in backend
- Run `uv sync` in the backend directory
- Check that virtual environment is activated (should happen automatically with uv)

### Frontend build errors
- Run `npm install` in the frontend directory
- Clear node_modules and reinstall if needed

## Security Notes

**Development Setup:**
- JWT secret is in .env.development (DO NOT commit to git)
- Cookies use `secure=False` for local HTTP development
- CORS allows http://localhost:5173

**For Production:**
- Generate a new JWT_SECRET_KEY (never reuse dev key)
- Set cookie `secure=True` (requires HTTPS)
- Update CORS origins to production domain
- Use environment-specific .env files

## Next Steps

Optional enhancements you can add:
- Add the PasswordChange component to TasksPage
- Add user profile page showing email and account info
- Add task sharing UI (assign tasks to other users)
- Add task filtering by status
- Add pagination for tasks list
- Add user search when assigning tasks
