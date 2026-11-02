# Desktop to Drive (Windows): a small window with the same actions as the macOS app.
# Saved as UTF-8 with BOM so Windows PowerShell 5.1 reads the Arabic text correctly.
. (Join-Path $PSScriptRoot 'common.ps1')
Add-Type -AssemblyName System.Windows.Forms, System.Drawing, Microsoft.VisualBasic
[System.Windows.Forms.Application]::EnableVisualStyles()
Set-Location $ToolDir

$Title = 'Desktop to Drive'
$Version = '1.1'
$Preview = Join-Path $ToolDir 'preview.txt'
$Log = Join-Path $ToolDir 'log.txt'
$Keep = Join-Path $ToolDir 'keep.txt'

function Show-Info($msg) {
    [System.Windows.Forms.MessageBox]::Show($msg, $Title, 'OK', 'Information') | Out-Null
}

function Confirm-Action($msg) {
    return ([System.Windows.Forms.MessageBox]::Show($msg, $Title, 'YesNo', 'Warning', 'Button2') -eq 'Yes')
}

function Invoke-Tool([string]$arguments, [string]$outFile = (Join-Path $env:TEMP 'desktop-to-drive-out.txt')) {
    # cmd redirection keeps the UTF-8 bytes that move.py writes (Arabic folder names)
    $py = Find-Python
    cmd /c "`"$($py.Console)`" `"$MoveScript`" $arguments > `"$outFile`" 2>&1"
    $code = $LASTEXITCODE
    $text = (Get-Content $outFile -Encoding UTF8 -ErrorAction SilentlyContinue) -join "`r`n"
    if ($code -ne 0) { throw $text }
    return $text
}

function Invoke-Preview {
    Invoke-Tool '--preview' $Preview | Out-Null
    return (Get-Content $Preview -Encoding UTF8 -TotalCount 1)
}

function Add-ToKeep([string[]]$paths) {
    foreach ($p in $paths) { Add-Content $Keep (Split-Path $p -Leaf) -Encoding UTF8 }
}

$actions = [ordered]@{
    'معاينة ما سيُنقل — Preview' = {
        Invoke-Preview | Out-Null
        Start-Process notepad $Preview
    }
    'النقل الآن — Move now' = {
        $summary = Invoke-Preview
        if ($summary -like '0 item*') { Show-Info "لا توجد عناصر تستوفي شروط النقل حاليًا.`r`nNothing to move now."; return }
        Start-Process notepad $Preview
        if (Confirm-Action "سيتم نقل العناصر التالية (قصّ لا نسخ) من سطح المكتب إلى Google Drive:`r`n$summary`r`n`r`nهل تريد المتابعة؟ — Move them now?") {
            Invoke-Tool '--now' | Out-Null
            Show-Info ("اكتملت العملية — Done`r`n`r`n" + (Get-Content $Log -Encoding UTF8 -Tail 1))
        }
    }
    'تفعيل النقل التلقائي كل ساعة — Turn on' = {
        if (Confirm-Action "ستنقل الأداة تلقائيًا كل ساعة العناصر التي لم تُعدَّل منذ المدة المحددة في الإعدادات.`r`nOld Desktop items will move every hour by themselves.`r`n`r`nهل تريد التفعيل؟ — Turn on?") {
            & (Join-Path $ToolDir 'start.ps1') | Out-Null
            Show-Info 'تم تفعيل النقل التلقائي — Automatic moving is ON'
        }
    }
    'إيقاف النقل التلقائي — Turn off' = {
        & (Join-Path $ToolDir 'stop.ps1') | Out-Null
        Show-Info 'تم إيقاف النقل التلقائي — Automatic moving is OFF'
    }
    'الإحصاءات — Statistics' = { Show-Info (Invoke-Tool '--stats') }
    'فتح مجلد الوجهة في Google Drive — Open Drive folder' = {
        try { $dest = Invoke-Tool '--where' } catch {
            throw "لم يُعثر على Google Drive. تأكد من تشغيل Google Drive for desktop وتسجيل الدخول.`r`nGoogle Drive not found. Make sure Google Drive for desktop is running and signed in."
        }
        Start-Process explorer $dest.Trim()
    }
    'استثناء ملفات من النقل — Exclude files' = {
        $dlg = New-Object System.Windows.Forms.OpenFileDialog
        $dlg.Multiselect = $true
        $dlg.InitialDirectory = [Environment]::GetFolderPath('Desktop')
        if ($dlg.ShowDialog() -eq 'OK') { Add-ToKeep $dlg.FileNames; Show-Info 'تمت الإضافة — Added' }
    }
    'استثناء مجلد من النقل — Exclude a folder' = {
        $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
        $dlg.SelectedPath = [Environment]::GetFolderPath('Desktop')
        if ($dlg.ShowDialog() -eq 'OK') { Add-ToKeep @($dlg.SelectedPath); Show-Info 'تمت الإضافة — Added' }
    }
    'تحرير قائمة المستثنيات — Edit excluded list' = {
        if (-not (Test-Path $Keep)) { New-Item -ItemType File $Keep | Out-Null }
        Start-Process notepad $Keep
    }
    'الإعدادات: الحد الأدنى لعمر الملف — Settings: minimum age' = {
        $days = [Microsoft.VisualBasic.Interaction]::InputBox("يُنقل العنصر فقط إذا لم يُعدَّل منذ عدد الأيام التالي (مثال: 1 أو 7 أو 0.5):`r`nMove an item only if it has not changed for this many days:", $Title, '1')
        if (-not $days) { return }
        $n = 0.0
        if (-not [double]::TryParse($days, [ref]$n)) { $n = -1 }
        try { Invoke-Tool ('--set-age ' + $n.ToString([Globalization.CultureInfo]::InvariantCulture)) | Out-Null } catch {
            throw "قيمة غير صالحة. أدخل رقمًا أكبر من 0 وحتى 365.`r`nInvalid value. Enter a number above 0, up to 365."
        }
        Show-Info "تم الحفظ — Saved: $days"
    }
    'فتح سجل العمليات — Open log' = {
        if (-not (Test-Path $Log)) { New-Item -ItemType File $Log | Out-Null }
        Start-Process notepad $Log
    }
    'حول الأداة — About' = {
        Show-Info "$Title $Version`r`n`r`nأداة مجانية تنقل العناصر القديمة من سطح المكتب إلى Google Drive وتنظّم الملفات المترابطة في مجلدات، دون استبدال أي ملف موجود.`r`n`r`nA free tool that moves old Desktop items to Google Drive, groups related files, and never overwrites anything.`r`n`r`nمجلد الأداة — Tool folder: $ToolDir"
    }
}

$form = New-Object System.Windows.Forms.Form
$form.Text = $Title
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$form.AutoSize = $true
$form.AutoSizeMode = 'GrowAndShrink'
$form.Padding = New-Object System.Windows.Forms.Padding(12)

$panel = New-Object System.Windows.Forms.FlowLayoutPanel
$panel.FlowDirection = 'TopDown'
$panel.AutoSize = $true
$panel.WrapContents = $false
$form.Controls.Add($panel)

$status = New-Object System.Windows.Forms.Label
$status.AutoSize = $true
$status.Margin = New-Object System.Windows.Forms.Padding(3, 3, 3, 12)
$status.Font = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
$panel.Controls.Add($status)

function Update-Status {
    if (Test-AutoOn) { $status.Text = 'النقل التلقائي: مُفعَّل — Automatic moving: ON'; $status.ForeColor = 'DarkGreen' }
    else { $status.Text = 'النقل التلقائي: متوقف — Automatic moving: OFF'; $status.ForeColor = 'DimGray' }
}

foreach ($name in $actions.Keys) {
    $b = New-Object System.Windows.Forms.Button
    $b.Text = $name
    $b.Width = 480
    $b.Height = 36
    $b.Tag = $actions[$name]
    $b.Add_Click({
        param($s)
        $form.UseWaitCursor = $true
        try { & $s.Tag }
        catch { [System.Windows.Forms.MessageBox]::Show("$_", $Title, 'OK', 'Error') | Out-Null }
        finally { $form.UseWaitCursor = $false; Update-Status }
    })
    $panel.Controls.Add($b)
}

Update-Status
[void]$form.ShowDialog()
