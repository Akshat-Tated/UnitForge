$ErrorActionPreference = 'Stop'
Write-Host "Waiting for server to start..."
Start-Sleep -Seconds 15

# 1. Register User
$registerBody = @{
    email = "testowner@example.com"
    password = "password123"
    name = "Test Owner"
} | ConvertTo-Json

Write-Host "Registering user..."
$regRes = Invoke-WebRequest -Uri "http://localhost:8080/api/auth/register" -Method POST -ContentType "application/json" -Body $registerBody -UseBasicParsing -ErrorAction Ignore

# 2. Login
$loginBody = @{
    email = "testowner@example.com"
    password = "password123"
} | ConvertTo-Json

Write-Host "Logging in..."
$loginRes = Invoke-WebRequest -Uri "http://localhost:8080/api/auth/login" -Method POST -ContentType "application/json" -Body $loginBody -UseBasicParsing
$token = ($loginRes.Content | ConvertFrom-Json).token
Write-Host "Got Token: $token"

# 3. Create Job
$jobBody = @{
    inputType = "python"
    inputPath = "/test/path"
    moduleMap = @{
        modules = @(
            @{ name = "test_module"; type = "python" }
        )
    }
} | ConvertTo-Json -Depth 10

Write-Host "Creating job..."
$jobRes = Invoke-WebRequest -Uri "http://localhost:8080/api/jobs" -Method POST -ContentType "application/json" -Headers @{ Authorization = "Bearer $token" } -Body $jobBody -UseBasicParsing
Write-Host "Job Response: "

# 4. Check Redis
Write-Host "Checking Redis task JSON..."
# Pop the latest task from the list
$redisPop = redis-cli.exe RPOP "unitforge:tasks"
Write-Host "Redis Task JSON: $redisPop"
