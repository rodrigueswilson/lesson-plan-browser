# Create Test User

## Quick Method: Use the Script

Run the script to create a test user:

```powershell
.\scripts\create_test_user.ps1
```

## Manual Method: Use Swagger UI

1. Open http://127.0.0.1:8000/api/docs
2. Find **POST /api/users** endpoint
3. Click **"Try it out"**
4. Enter user data:
   ```json
   {
     "first_name": "Test",
     "last_name": "User",
     "email": "test@example.com"
   }
   ```
5. Click **"Execute"**

## Manual Method: Use curl

```powershell
$body = @{
    first_name = "Test"
    last_name = "User"
    email = "test@example.com"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/users" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

## Verify Users

After creating a user, check:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/users | Select-Object -ExpandProperty Content
```

Should return a JSON array with the user(s).

## Frontend

Once users are created, refresh the frontend at http://localhost:1420 and you should see the users listed.

