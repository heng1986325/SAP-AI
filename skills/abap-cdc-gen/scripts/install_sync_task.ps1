# Install Feishu Checklist Sync Task in Windows Task Scheduler
# Run this script ONCE per machine to set up automatic sync.
# Usage: powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\abap-cdc-gen\scripts\install_sync_task.ps1"
#        （从安装后的技能目录执行；Codex 用户把 .claude 换成 .codex）
#
# After installation, the task runs:
#   - Weekdays at 9:17 and 14:17 (CST)
#   - Silently in background (no console window)
#   - With the current user's permissions

$ErrorActionPreference = "Stop"

$taskName = "ABAP_FeishuChecklistSync"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = "$scriptDir\feishu_sync.bat"

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[Install] Removing existing task '$taskName'..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create task action
$action = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $scriptDir

# Create triggers: weekdays at 9:17 and 14:17
$trigger1 = New-ScheduledTaskTrigger -Daily -At "09:17" -DaysInterval 1
$trigger2 = New-ScheduledTaskTrigger -Daily -At "14:17" -DaysInterval 1

# Set weekly repetition for weekdays only
$trigger1.DaysOfWeek = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
$trigger2.DaysOfWeek = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

# Settings: hidden, no password required, don't run if on battery
$settings = New-ScheduledTaskSettingsSet `
    -Hidden `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

# Register with current user
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger1, $trigger2 `
    -Settings $settings `
    -Principal $principal `
    -Description "Sync Feishu Bitable '14.标准化清单_OP&PCE' to local markdown file for ABAP development checklist lookup" `
    -Force

Write-Host "[Install] Task '$taskName' installed successfully."
Write-Host "[Install] Triggers: Mon-Fri at 09:17 and 14:17"
Write-Host "[Install] Script: $batPath"
Write-Host ""
Write-Host "To verify:  taskschd.msc  →  look for '$taskName'"
Write-Host "To run now: Start-ScheduledTask -TaskName '$taskName'"
Write-Host "To remove:  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"