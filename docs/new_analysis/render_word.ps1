param([Parameter(Mandatory=$true)][string]$RunDirectory)
$ErrorActionPreference = 'Stop'
$resolvedRun = (Resolve-Path -LiteralPath $RunDirectory).Path
$expectedRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../results/new')).Path
if (-not $resolvedRun.StartsWith($expectedRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Render output must stay in a project results/new run.'
}
$qaDirectory = Join-Path $resolvedRun 'qa'
New-Item -ItemType Directory -Force -Path $qaDirectory | Out-Null
$documents = @(Get-Item -LiteralPath (Join-Path $resolvedRun 'results/Model_exploration_predicted_vs_observed.docx'))
$documents += @(Get-ChildItem -LiteralPath (Join-Path $resolvedRun 'results/paper') -Filter '*.docx')
$word = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    foreach ($file in $documents) {
        $document = $null
        try {
            $document = $word.Documents.Open($file.FullName, $false, $true)
            $document.Repaginate()
            $pdfPath = Join-Path $qaDirectory ($file.BaseName + '.pdf')
            $document.ExportAsFixedFormat($pdfPath, 17)
            Write-Output ($file.Name + ' -> ' + $pdfPath)
        } finally {
            if ($null -ne $document) {
                $document.Close(0)
                [Runtime.InteropServices.Marshal]::ReleaseComObject($document) | Out-Null
            }
        }
    }
} finally {
    if ($null -ne $word) {
        $word.Quit()
        [Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    }
}
