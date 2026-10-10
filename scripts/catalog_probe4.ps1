# D:\tmp\catalog_probe4.ps1 - ScrollPattern 确定性扫掠 + 按钮 dump + 导入探查
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class M7 {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, int e);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  public static void Click(int x, int y) { SetCursorPos(x,y); System.Threading.Thread.Sleep(90); mouse_event(0x0002,0,0,0,0); System.Threading.Thread.Sleep(50); mouse_event(0x0004,0,0,0,0); }
  public static void Wheel(int delta) { mouse_event(0x0800, 0, 0, (uint)delta, 0); }
  public static void Key(byte vk) { keybd_event(vk,0,0,UIntPtr.Zero); System.Threading.Thread.Sleep(40); keybd_event(vk,0,2,UIntPtr.Zero); }
}
"@

$procId = 5448
$root = [System.Windows.Automation.AutomationElement]::RootElement
$out = New-Object System.Collections.Generic.List[string]
function Log($s) { $out.Add([string]$s); Write-Output $s }

function Get-Catalog {
  $cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty, $procId)
  $wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
  foreach ($w in $wins) { if ($w.Current.Name -eq '对象目录') { return $w } }
  return $null
}
$catWin = Get-Catalog
if (-not $catWin) { Log 'NOT FOUND'; exit 1 }

function Get-Items($win) {
  $lc = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::List)
  $list = $win.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $lc)
  if (-not $list) { return ,(New-Object System.Collections.Generic.List[string]) }
  $lis = $list.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::ListItem)))
  $names = New-Object System.Collections.Generic.List[string]
  $tc = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Text)
  foreach ($li in $lis) {
    $t = $li.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $tc)
    if ($t -and $t.Current.Name) { $names.Add($t.Current.Name) }
  }
  return ,$names
}
function Get-ListEl($win) {
  $lc = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::List)
  return $win.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $lc)
}
function Click-Category([string]$name) {
  $win = Get-Catalog
  $btns = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)))
  foreach ($b in $btns) {
    $bt = $b.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Text)))
    if ($bt -and $bt.Current.Name -eq $name) {
      try { $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke(); return 'inv' } catch {}
      $r = $b.Current.BoundingRectangle
      [M7]::Click([int]($r.X + $r.Width/2), [int]($r.Y + $r.Height/2)); return 'mouse'
    }
  }
  return 'NOTFOUND'
}

function Sweep-Category([string]$cat) {
  Click-Category $cat | Out-Null
  Start-Sleep -Milliseconds 1400
  $win = Get-Catalog
  $list = Get-ListEl $win
  if (-not $list) { return $null }
  $sp = $null
  try { $sp = $list.GetCurrentPattern([System.Windows.Automation.ScrollPattern]::Pattern) } catch { $sp = $null }
  $seen = New-Object System.Collections.Generic.HashSet[string]
  $names = New-Object System.Collections.Generic.List[string]
  $trace = New-Object System.Collections.Generic.List[string]
  if ($sp) {
    $proc = @(0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60, 63, 66, 69, 72, 75, 78, 81, 84, 87, 90, 93, 96, 99, 100)
    foreach ($v in $proc) {
      try { $sp.SetScrollPercent([double](-1), [double]$v) } catch { }
      Start-Sleep -Milliseconds 320
      $items = Get-Items (Get-Catalog)
      Start-Sleep -Milliseconds 180
      $items2 = Get-Items (Get-Catalog)
      $before = $seen.Count
      foreach ($n in $items) { if ($seen.Add($n)) { $names.Add($n) } }
      foreach ($n in $items2) { if ($seen.Add($n)) { $names.Add($n) } }
      $trace.Add("$v%:+$($seen.Count - $before)")
    }
    return [pscustomobject]@{ names = $names; mode = 'scrollPattern'; trace = ($trace -join ' ') }
  } else {
    # wheel fallback
    $r = $list.Current.BoundingRectangle
    $cx = [int]($r.X + $r.Width/2); $cy = [int]($r.Y + $r.Height/2)
    [M7]::SetCursorPos($cx, $cy)
    for ($i = 0; $i -lt 40; $i++) { [M7]::Wheel(360) }
    Start-Sleep -Milliseconds 700
    $stall = 0
    for ($round = 0; $round -lt 100; $round++) {
      $items = Get-Items (Get-Catalog)
      $before = $seen.Count
      foreach ($n in $items) { if ($seen.Add($n)) { $names.Add($n) } }
      if ($seen.Count -eq $before) { $stall++ } else { $stall = 0 }
      if ($stall -ge 4) { break }
      [M7]::SetCursorPos($cx, $cy)
      [M7]::Wheel(-600)
      Start-Sleep -Milliseconds 500
    }
    return [pscustomobject]@{ names = $names; mode = 'wheel'; trace = "rounds=$round" }
  }
}

Log "=== ScrollPattern 扫掠全部 7 类 ==="
$cats = @('家居家具','办公家具','卫生间','店面設計','外部規劃','道路規劃','其他')
$uiData = @{}
foreach ($c in $cats) {
  $res = Sweep-Category $c
  if ($res) {
    $uiData[$c] = $res.names
    Log "--- [$c] mode=$($res.mode) total=$($res.names.Count)"
    Log "    trace: $($res.trace)"
    Log ("    " + (($res.names) -join ' / '))
  }
}
$uiData.GetEnumerator() | ForEach-Object { }
# 存 JSON（数组形式）
$obj = @{}
foreach ($k in $uiData.Keys) { $obj[$k] = @($uiData[$k]) }
$obj | ConvertTo-Json -Depth 4 | Out-File 'D:\tmp\ui_categories.json' -Encoding utf8

Log ""
Log "=== 按钮全量 dump ==="
$win = Get-Catalog
$btns = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)))
$bi = 0
foreach ($b in $btns) {
  $bt = $b.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Text)))
  $tn = if ($bt) { $bt.Current.Name } else { '' }
  $r = $b.Current.BoundingRectangle
  Log "  btn[$bi] name='$($b.Current.Name)' text='$tn' rect=$([int]$r.X),$([int]$r.Y),$([int]$r.Width)x$([int]$r.Height)"
  $bi++
}

$out | Out-File -FilePath 'D:\tmp\catalog_probe4_out.txt' -Encoding utf8
Write-Output "DONE"
