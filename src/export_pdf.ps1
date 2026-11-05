# Exports outputs/card_activation_deck.pptx to PDF using the installed PowerPoint (Windows only).
# Usage:  powershell -ExecutionPolicy Bypass -File src/export_pdf.ps1
$root = Split-Path -Parent $PSScriptRoot
$pptx = Join-Path $root "outputs\card_activation_deck.pptx"
$pdf  = Join-Path $root "outputs\card_activation_deck.pdf"
$ppt = New-Object -ComObject PowerPoint.Application
$deck = $ppt.Presentations.Open($pptx, $true, $false, $false)
$deck.SaveAs($pdf, 32)   # 32 = ppSaveAsPDF
$deck.Close()
$ppt.Quit()
Write-Output "Saved $pdf"
