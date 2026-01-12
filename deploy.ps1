$Server = "192.168.50.150"
$User = Read-Host "Enter SSH Username for $Server (e.g. repeater or root)"

Write-Host "1. Packing files..."
# Create a tarball to avoid copying .git, venv, and permission issues
# Windows tar supports exclusions
tar --exclude ".git" --exclude "venv" --exclude "__pycache__" -cf package.tar .

Write-Host "2. Transferring package..."
scp package.tar "$($User)@$($Server):~"

if ($LASTEXITCODE -ne 0) {
    Write-Error "SCP failed. Please check connectivity and credentials."
    exit
}

Write-Host "3. Installing System Dependencies and Python Environment..."
# Updated remote script to handle tar unpacking
$RemoteScript = @'
echo '--- unpacking ---'
mkdir -p ~/asl3_wx_announce
mv ~/package.tar ~/asl3_wx_announce/
cd ~/asl3_wx_announce
tar -xf package.tar
rm package.tar


echo '--- Fixing Hostname ---'
sudo bash -c 'grep -q "$(hostname)" /etc/hosts || echo "127.0.0.1 $(hostname)" >> /etc/hosts'

echo '--- Updating Apt ---'
sudo apt update
sudo apt install -y python3-pip python3-venv libttspico-utils gpsd sox libsox-fmt-all

echo '--- Setting up Venv ---'
cd ~/asl3_wx_announce
python3 -m venv venv
source venv/bin/activate

echo '--- Installing Python Libs ---'
pip install -r requirements.txt

echo '--- DEBUG ENV_CANADA ---'
./venv/bin/python3 debug_ec.py

echo '--- Running Test Report ---'
# Run using the venv python
sudo ./venv/bin/python3 -m asl3_wx_announce.main --config config.yaml --report
'@

# Sanitize script for Linux (Remove Carriage Returns)
$RemoteScript = $RemoteScript -replace "`r", ""

# Base64 Encode to avoid quoting hell
$ScriptBytes = [System.Text.Encoding]::UTF8.GetBytes($RemoteScript)
$ScriptBase64 = [Convert]::ToBase64String($ScriptBytes)

# Execute via base64 decode
ssh -t "$($User)@$($Server)" "echo $ScriptBase64 | base64 -d | bash"
