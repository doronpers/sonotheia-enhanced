$ErrorActionPreference = "Stop"

$API_URL = "http://localhost:8000"

Write-Host "Testing API endpoints..."
Write-Host ""

# Test health
Write-Host "1. Health check:"
try {
    $health = Invoke-RestMethod -Uri "$API_URL/api/v1/health" -Method Get
    Write-Host ($health | ConvertTo-Json -Depth 5)
} catch {
    Write-Host "Backend not running or health check failed: $_"
    exit 1
}
Write-Host ""

# Test session creation
Write-Host "2. Creating session:"
$sessionBody = @{
    user_id = "TEST-001"
    session_type = "onboarding"
} | ConvertTo-Json

$sessionResponse = Invoke-RestMethod -Uri "$API_URL/api/session/start" -Method Post -Body $sessionBody -ContentType "application/json"
Write-Host ($sessionResponse | ConvertTo-Json -Depth 5)
$sessionId = $sessionResponse.session_id
Write-Host ""

if ($sessionId) {
    Write-Host "3. Updating with biometric data:"
    $bioBody = @{
        document_verified = $true
        face_match_score = 0.95
        liveness_passed = $true
        incode_session_id = "test-123"
    } | ConvertTo-Json
    
    $bioResponse = Invoke-RestMethod -Uri "$API_URL/api/session/$sessionId/biometric" -Method Post -Body $bioBody -ContentType "application/json"
    Write-Host ($bioResponse | ConvertTo-Json -Depth 5)
    Write-Host ""
    
    Write-Host "4. Updating with voice data:"
    $voiceBody = @{
        deepfake_score = 0.15
        speaker_verified = $true
        speaker_score = 0.96
        audio_quality = 0.85
        audio_duration_seconds = 4.5
    } | ConvertTo-Json
    
    $voiceResponse = Invoke-RestMethod -Uri "$API_URL/api/session/$sessionId/voice" -Method Post -Body $voiceBody -ContentType "application/json"
    Write-Host ($voiceResponse | ConvertTo-Json -Depth 5)
    Write-Host ""
    
    Write-Host "5. Evaluating risk:"
    $evalBody = @{
        session_id = $sessionId
        include_factors = $true
    } | ConvertTo-Json
    
    $evalResponse = Invoke-RestMethod -Uri "$API_URL/api/session/$sessionId/evaluate" -Method Post -Body $evalBody -ContentType "application/json"
    Write-Host ($evalResponse | ConvertTo-Json -Depth 5)
    Write-Host ""
}

Write-Host "[OK] API tests complete"
