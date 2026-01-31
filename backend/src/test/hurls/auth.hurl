# Authentication Tests

# Test 1: Login with invalid credentials should return 401
POST http://{{host}}:{{port}}/api/v1/auth/login
Content-Type: application/json
{
  "username": "invaliduser",
  "password": "wrongpassword"
}

HTTP 401
[Asserts]
jsonpath "$.detail" exists


# Test 2: Login with valid credentials should return 200 and tokens
POST http://{{host}}:{{port}}/api/v1/auth/login
Content-Type: application/json
{
  "username": "user1",
  "password": "password123"
}

HTTP 200
[Captures]
access_token: jsonpath "$.access_token"
refresh_token: jsonpath "$.refresh_token"
[Asserts]
jsonpath "$.access_token" exists
jsonpath "$.refresh_token" exists
jsonpath "$.token_type" == "bearer"
cookie "access_token" exists
cookie "refresh_token" exists


# Test 3: Access protected endpoint without auth should return 401
GET http://{{host}}:{{port}}/api/v1/auth/me

HTTP 401


# Test 4: Access protected endpoint with valid auth should return user info
GET http://{{host}}:{{port}}/api/v1/auth/me
Cookie: access_token={{access_token}}

HTTP 200
[Asserts]
jsonpath "$.username" exists
jsonpath "$.email" exists


# Test 5: Get tasks with valid auth should work
GET http://{{host}}:{{port}}/api/v1/tasks/
Cookie: access_token={{access_token}}

HTTP 200


# Test 6: Refresh token should work
POST http://{{host}}:{{port}}/api/v1/auth/refresh
Cookie: refresh_token={{refresh_token}}

HTTP 200
[Captures]
new_access_token: jsonpath "$.access_token"
[Asserts]
jsonpath "$.access_token" exists
jsonpath "$.refresh_token" exists


# Test 7: Change password with invalid current password should fail
POST http://{{host}}:{{port}}/api/v1/auth/change-password
Cookie: access_token={{new_access_token}}
Content-Type: application/json
{
  "current_password": "wrongpassword",
  "new_password": "newpassword123"
}

HTTP 400


# Test 8: Change password with short new password should fail
POST http://{{host}}:{{port}}/api/v1/auth/change-password
Cookie: access_token={{new_access_token}}
Content-Type: application/json
{
  "current_password": "password123",
  "new_password": "short"
}

HTTP 400


# Test 9: Logout should clear cookies
POST http://{{host}}:{{port}}/api/v1/auth/logout

HTTP 200
[Asserts]
jsonpath "$.message" == "Successfully logged out"
