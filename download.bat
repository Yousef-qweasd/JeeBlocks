$ReqFile = "J:\System\Programing_Projects\Prog_Bock\static\JeeBlocks\languages\python\Lib\requirements.txt"
$Dest    = "J:\System\Programing_Projects\Prog_Bock\static\JeeBlocks\languages\python\Lib"
$FailedFile = "J:\System\Programing_Projects\Prog_Bock\static\JeeBlocks\languages\python\Lib\failed.txt"
# ==========================================
# الإعدادات
# ==========================================
$MaxAttempts = 5
# مدة الانتظار بين المحاولات
$RetryDelay = 10
# مدة الانتظار عندما يكون الإنترنت مفصولًا
$InternetRetryDelay = 15
# ==========================================
# إنشاء المجلدات والملفات
# ==========================================
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
if (-not (Test-Path $FailedFile)) {
    New-Item -ItemType File -Path $FailedFile -Force | Out-Null
}
# ==========================================
# اختبار الاتصال بـ PyPI
# ==========================================
function Test-PyPI {
    try {
        $Response = Invoke-WebRequest `
            -Uri "https://pypi.org/simple/" `
            -Method Head `
            -TimeoutSec 15 `
            -UseBasicParsing `
            -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}
# ==========================================
# تسجيل المكتبة الفاشلة
# ==========================================
function Add-FailedPackage {
    param (
        [string]$Package,
        [string]$Reason
    )
    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content `
        -Path $FailedFile `
        -Value "[$Time] $Package | $Reason" `
        -Encoding UTF8
}
# ==========================================
# البرنامج الرئيسي
# ==========================================
while ($true) {
    Clear-Host
    # ======================================
    # قراءة المكتبات المتبقية
    # ======================================
    $Packages = @(
        Get-Content $ReqFile |
        Where-Object {
            $_.Trim() -ne "" -and
            -not $_.Trim().StartsWith("#")
        }
    )
    # ======================================
    # انتهت كل المكتبات
    # ======================================
    if ($Packages.Count -eq 0) {
        Write-Host ""
        Write-Host "======================================" -ForegroundColor Green
        Write-Host "       تم الانتهاء من كل المكتبات" -ForegroundColor Green
        Write-Host "======================================" -ForegroundColor Green
        Write-Host ""
        break
    }
    # ======================================
    # أخذ أول مكتبة
    # ======================================
    $Package = $Packages[0].Trim()
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host "جاري تنزيل: $Package" -ForegroundColor Yellow
    Write-Host "المتبقي: $($Packages.Count)" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host ""
    $Success = $false
    $DefinitiveFailure = $false
    $LastError = ""
    # ======================================
    # المحاولات
    # ======================================
    for ($Attempt = 1; $Attempt -le $MaxAttempts; $Attempt++) {
        Write-Host ""
        Write-Host "--------------------------------------" -ForegroundColor DarkCyan
        Write-Host "المحاولة $Attempt من $MaxAttempts" -ForegroundColor Magenta
        Write-Host "--------------------------------------" -ForegroundColor DarkCyan
        # ==================================
        # محاولة التنزيل
        # ==================================
        $PipOutput = @(
            & python -m pip download `
                --dest "$Dest" `
                --timeout 120 `
                --retries 5 `
                "$Package" 2>&1
        )
        $ExitCode = $LASTEXITCODE
        # عرض نتيجة pip
        $PipOutput | ForEach-Object {
            Write-Host $_
        }
        # ==================================
        # نجح التنزيل
        # ==================================
        if ($ExitCode -eq 0) {
            $Success = $true
            Write-Host ""
            Write-Host "نجح تنزيل: $Package" -ForegroundColor Green
            break
        }
        # ==================================
        # حفظ آخر خطأ
        # ==================================
        $LastError = ($PipOutput -join " ")
        Write-Host ""
        Write-Host "فشل التنزيل." -ForegroundColor Red
        # ==================================
        # فحص الإنترنت
        # ==================================
        Write-Host "جاري فحص الاتصال بـ PyPI..." -ForegroundColor Yellow
        $InternetOK = Test-PyPI
        # ==================================
        # الإنترنت مفصول
        # ==================================
        if (-not $InternetOK) {
            Write-Host ""
            Write-Host "======================================" -ForegroundColor Red
            Write-Host "        الاتصال بـ PyPI غير متاح" -ForegroundColor Red
            Write-Host "======================================" -ForegroundColor Red
            Write-Host ""
            Write-Host "لن يتم حذف: $Package" -ForegroundColor Yellow
            Write-Host "سيتم الانتظار حتى يعود الإنترنت..." -ForegroundColor Cyan
            # ==================================
            # الانتظار إلى أن يعود الإنترنت
            # ==================================
            while (-not (Test-PyPI)) {
                Write-Host ""
                Write-Host "الإنترنت ما زال غير متاح..." -ForegroundColor DarkYellow
                Write-Host "إعادة الفحص بعد $InternetRetryDelay ثانية..." -ForegroundColor DarkYellow
                Start-Sleep -Seconds $InternetRetryDelay
            }
            # ==================================
            # عاد الإنترنت
            # ==================================
            Write-Host ""
            Write-Host "======================================" -ForegroundColor Green
            Write-Host "        عاد الاتصال بالإنترنت" -ForegroundColor Green
            Write-Host "======================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "لن يتم حذف المكتبة." -ForegroundColor Green
            Write-Host "سيتم إعادة المحاولة: $Package" -ForegroundColor Cyan
            # ==================================
            # مهم جدًا:
            # لا نحسب انقطاع الإنترنت كمحاولة
            # ==================================
            $Attempt--
            Start-Sleep -Seconds 2
            continue
        }
        # ==================================
        # الإنترنت يعمل
        # ==================================
        Write-Host ""
        Write-Host "الاتصال بـ PyPI يعمل." -ForegroundColor Green
        # ==================================
        # لو وصلنا هنا:
        # الإنترنت موجود، لكن pip فشل
        # ==================================
        if ($Attempt -lt $MaxAttempts) {
            Write-Host ""
            Write-Host "المشكلة ليست انقطاع الإنترنت." -ForegroundColor Yellow
            Write-Host "سيتم إعادة المحاولة بعد $RetryDelay ثواني..." -ForegroundColor Cyan
            Start-Sleep -Seconds $RetryDelay
            continue
        }
        # ==================================
        # انتهت المحاولات
        # ==================================
        Write-Host ""
        Write-Host "======================================" -ForegroundColor Red
        Write-Host "     فشل تنزيل المكتبة نهائيًا" -ForegroundColor Red
        Write-Host "======================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "المكتبة: $Package" -ForegroundColor Yellow
        Write-Host "تم استنفاد $MaxAttempts محاولات." -ForegroundColor Red
        $DefinitiveFailure = $true
        break
    }
    # ======================================
    # نجاح
    # ======================================
    if ($Success) {
        # حذف المكتبة من requirements
        $Remaining = @(
            $Packages | Select-Object -Skip 1
        )
        Set-Content `
            -Path $ReqFile `
            -Value $Remaining `
            -Encoding UTF8
        Write-Host ""
        Write-Host "تم حذف $Package من requirements.txt" -ForegroundColor Green
        Write-Host "الانتقال للمكتبة التالية..." -ForegroundColor Cyan
        Start-Sleep -Seconds 2
        continue
    }
    # ======================================
    # فشل نهائي
    # ======================================
    if ($DefinitiveFailure) {
        # ==================================
        # تسجيل المكتبة في failed.txt
        # ==================================
        $Reason = $LastError
        # تقليل حجم السطر في failed.txt
        if ($Reason.Length -gt 1000) {
            $Reason = $Reason.Substring(0, 1000)
        }
        Add-FailedPackage `
            -Package $Package `
            -Reason $Reason
        Write-Host ""
        Write-Host "تم تسجيل المكتبة في failed.txt" -ForegroundColor Yellow
        # ==================================
        # حذف المكتبة من requirements
        # ==================================
        $Remaining = @(
            $Packages | Select-Object -Skip 1
        )
        Set-Content `
            -Path $ReqFile `
            -Value $Remaining `
            -Encoding UTF8
        Write-Host ""
        Write-Host "تم حذف $Package من requirements.txt" -ForegroundColor Yellow
        Write-Host "سيتم الانتقال للمكتبة التالية..." -ForegroundColor Cyan
        Start-Sleep -Seconds 2
        continue
    }
}