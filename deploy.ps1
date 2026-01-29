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
# Changed to use sudo for /opt/ access
# Also chown to user so they can run without sudo if desired, or keep root. 
# Service runs as root usually.
$REMOTE_CMD = "sudo mkdir -p ${REMOTE_PATH} && sudo tar -xvf /tmp/${TAR_FILE} -C ${REMOTE_PATH} && rm /tmp/${TAR_FILE} && sudo pip3 install --break-system-packages -r ${REMOTE_PATH}/requirements.txt && sudo cp ${REMOTE_PATH}/asl3-wx.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable asl3-wx && sudo systemctl restart asl3-wx"
ssh ${REMOTE_USER}@${REMOTE_HOST} $REMOTE_CMD

# 4. Cleanup local artifact
Remove-Item $TAR_FILE

Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "To run the code:"
Write-Host "  ssh ${REMOTE_USER}@${REMOTE_HOST}"
Write-Host "  cd ${REMOTE_PATH}"
Write-Host "  sudo python3 -m asl3_wx_announce.main"
