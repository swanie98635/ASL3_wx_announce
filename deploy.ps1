# Deploy ASL3 WX Announce to Remote Node
# USAGE: .\deploy.ps1

# --- CONFIGURATION (PLEASE EDIT THESE) ---
$REMOTE_HOST = "192.168.50.61"      # REPLACE with your Node's IP address
$REMOTE_USER = "admin"            # REPLACE with your SSH username (e.g. repeater, root, admin)
$REMOTE_PATH = "/opt/asl3_wx_announce" # Standard location
# -----------------------------------------

Write-Host "Deploying to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}..." -ForegroundColor Cyan

# 1. Create a local tar archive of the files to minimise SCP calls (and password prompts)
Write-Host "Bundling files..."
$TAR_FILE = "deploy_package.tar"
tar -cvf $TAR_FILE asl3_wx_announce requirements.txt config.yaml diagnose_audio.py asl3-wx.service

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error creating tar archive." -ForegroundColor Red
    exit
}

# 2. Upload the tar archive (Prompt #1)
Write-Host "Uploading package (You may be asked for your password)..."
scp $TAR_FILE ${REMOTE_USER}@${REMOTE_HOST}:/tmp/$TAR_FILE
if ($LASTEXITCODE -ne 0) {
    Write-Host "SCP failed. Check connection." -ForegroundColor Red
    exit
}

# 3. Extract on remote server (Prompt #2)
Write-Host "Extracting on remote server (You may be asked for your password again)..."
# Service runs as root usually.
# 1. Create directory
# 2. Extract
# 3. Create venv if not exists
# 4. Install requirements in venv
# 5. Setup service
$REMOTE_CMD = "sudo mkdir -p ${REMOTE_PATH} && sudo tar -xvf /tmp/${TAR_FILE} -C ${REMOTE_PATH} && rm /tmp/${TAR_FILE} && sudo python3 -m venv ${REMOTE_PATH}/venv && sudo ${REMOTE_PATH}/venv/bin/pip install -r ${REMOTE_PATH}/requirements.txt && sudo cp ${REMOTE_PATH}/asl3-wx.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable asl3-wx && sudo systemctl restart asl3-wx"
ssh ${REMOTE_USER}@${REMOTE_HOST} $REMOTE_CMD

# 4. Cleanup local artifact
Remove-Item $TAR_FILE

Write-Host "Deployment Complete! The 'asl3-wx' service is running in the background." -ForegroundColor Green
Write-Host "To check status/logs:"
Write-Host "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'sudo systemctl status asl3-wx'"
Write-Host "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'sudo journalctl -u asl3-wx -f'"
Write-Host "To stop:"
Write-Host "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'sudo systemctl stop asl3-wx'"

# --- Display Config Summary ---
Write-Host ""
Write-Host "--- Configuration Summary ---" -ForegroundColor Yellow

$configContent = Get-Content config.yaml -Raw

# Helper function for regex extraction
function Get-ConfigValue {
    param ($pattern, $default = "Unknown")
    if ($configContent -match $pattern) { return $Matches[1].Trim('"').Trim("'") }
    return $default
}

$callsign = Get-ConfigValue "callsign:\s*(.*)"
$check_int = Get-ConfigValue "check_interval_minutes:\s*(\d+)"
$active_int = Get-ConfigValue "active_check_interval_minutes:\s*(\d+)"
$timezone = Get-ConfigValue "timezone:\s*(.*)"
$hourly_enabled = Get-ConfigValue "hourly_report:\s*\n\s*enabled:\s*(true|false)" "false"
$hourly_minute = Get-ConfigValue "minute:\s*(\d+)"

Write-Host "Callsign:          $callsign"
Write-Host "Timezone:          $timezone"
Write-Host "Check Interval:    $check_int minutes (Normal)"
Write-Host "Active Interval:   $active_int minutes (During Alerts)"

if ($hourly_enabled -eq "true") {
    Write-Host "Hourly Report:     Enabled (at minute $hourly_minute)"
    
    # Parse Content flags
    $content_keys = "time", "time_error", "conditions", "forecast", "forecast_verbose", "astro", "solar_flux", "status", "code_source"
    $enabled_content = @()
    foreach ($key in $content_keys) {
        if ($configContent -match "${key}:\s*true") {
            $enabled_content += $key
        }
    }
    $content_str = $enabled_content -join ", "
    Write-Host "Hourly Content:    $content_str"
}
else {
    Write-Host "Hourly Report:     Disabled"
}
Write-Host "-----------------------------"
Write-Host ""
