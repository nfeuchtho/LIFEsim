# Build a latexdiff PDF between two revisions of thesis/main.tex.
# Usage:
#   .\make-diff.ps1                 # diff HEAD vs working tree
#   .\make-diff.ps1 -OldRef abc123   # diff a specific commit/tag vs working tree
#   .\make-diff.ps1 -OldRef abc123 -NewRef def456
#   .\make-diff.ps1 -OldFile revisions\supervisor_read_2026-07-10.tex
#
# Windows TeX Live's latexdiff.exe/latexmk.exe wrappers are missing runscript.dll
# on this machine, so we call the bundled perl directly against the .pl script.
#
# main.tex contains many adjacent-inline-math pairs like "s$^{-1}$$\upmu$m"
# (a literal "$$" from two $...$ runs touching). latexdiff's tokenizer misreads
# that as a display-math delimiter and corrupts everything after it in the
# diff output (manifests as a "Runaway argument"/unmatched-brace pdflatex
# error far from the actual edit). Fix: in temp copies only (never the
# tracked main.tex), insert an invisible {} between the two $ signs before
# diffing, then diff those. Purely cosmetic, renders identically.

param(
    [string]$OldRef = "HEAD",
    [string]$OldFile = "",
    [string]$NewRef = ""
)

$ErrorActionPreference = "Stop"

$TlBin    = "C:\texlive\2024\bin\windows"
$TlPerl   = "C:\texlive\2024\tlpkg\tlperl\bin"
$LdScript = "C:\texlive\2024\texmf-dist\scripts\latexdiff\latexdiff.pl"

$env:PATH = "$TlBin;$TlPerl;$env:PATH"

$ThesisDir = Split-Path -Parent $PSScriptRoot
$RepoRoot  = Split-Path -Parent $ThesisDir
$TmpDir    = Join-Path $ThesisDir ".diff_tmp"

New-Item -ItemType Directory -Force -Path $TmpDir | Out-Null

$OldTex = Join-Path $TmpDir "main_old.tex"
$NewTex = Join-Path $TmpDir "main_new.tex"

Push-Location $RepoRoot
try {
    if ($OldFile -ne "") {
        if ([System.IO.Path]::IsPathRooted($OldFile)) {
            $ResolvedOldFile = $OldFile
        } else {
            $ResolvedOldFile = Join-Path $ThesisDir $OldFile
        }

        if (-not (Test-Path -LiteralPath $ResolvedOldFile -PathType Leaf)) {
            throw "OldFile does not exist: $ResolvedOldFile"
        }

        Copy-Item -LiteralPath $ResolvedOldFile -Destination $OldTex -Force
    } else {
        git show "${OldRef}:thesis/main.tex" | Out-File -Encoding utf8 $OldTex
    }

    if ($NewRef -eq "") {
        Copy-Item (Join-Path $ThesisDir "main.tex") $NewTex -Force
    } else {
        git show "${NewRef}:thesis/main.tex" | Out-File -Encoding utf8 $NewTex
    }
} finally {
    Pop-Location
}

# Neutralize adjacent "$$" (see comment at top) so latexdiff's tokenizer
# doesn't mistake it for display math.
(Get-Content $OldTex -Raw) -replace '\$\$', '${}$' | Set-Content -Encoding utf8 -NoNewline $OldTex
(Get-Content $NewTex -Raw) -replace '\$\$', '${}$' | Set-Content -Encoding utf8 -NoNewline $NewTex

# A deleted label can still be referenced by unchanged text in the old side of
# a latexdiff document.  Keep a generated compatibility anchor in the diff
# only, so those deleted references do not render as ?? in the supervisor PDF.
function Get-LabelNames([string]$TexPath) {
    $labels = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $tex = [System.IO.File]::ReadAllText($TexPath)

    foreach ($match in [regex]::Matches($tex, '\\label\s*\{([^}]*)\}')) {
        [void]$labels.Add($match.Groups[1].Value)
    }

    Write-Output -NoEnumerate $labels
}

$OldLabels = Get-LabelNames $OldTex
$NewLabels = Get-LabelNames $NewTex
$CompatibilityLabels = @($OldLabels | Where-Object { -not $NewLabels.Contains($_) } | Sort-Object)

$DiffTex = Join-Path $ThesisDir "main_diff.tex"
perl $LdScript $OldTex $NewTex | Out-File -Encoding utf8 $DiffTex

if ($LASTEXITCODE -ne 0) {
    Write-Error "latexdiff failed"
    exit 1
}

if ($CompatibilityLabels.Count -gt 0) {
    $diff = [System.IO.File]::ReadAllText($DiffTex)
    $documentMarker = '\begin{document}'
    $documentIndex = $diff.IndexOf($documentMarker, [System.StringComparison]::Ordinal)

    if ($documentIndex -lt 0) {
        throw "Could not find \\begin{document} in generated diff source"
    }

    $anchors = [string]::Join(
        [Environment]::NewLine,
        @($CompatibilityLabels | ForEach-Object { "\phantomsection\label{$($_)}" })
    )
    $insertion = $documentMarker + [Environment]::NewLine +
        "% Compatibility labels for references deleted in the new revision." + [Environment]::NewLine +
        $anchors

    $diff = $diff.Substring(0, $documentIndex) + $insertion +
        $diff.Substring($documentIndex + $documentMarker.Length)
    [System.IO.File]::WriteAllText($DiffTex, $diff, [System.Text.UTF8Encoding]::new($false))
    Write-Output "Compatibility labels inserted: $($CompatibilityLabels -join ', ')"
}

# latexdiff can wrap a changed tabular declaration in FL markup.  The closing
# markup then lands between \begin{tabular} and \toprule, where booktabs'
# \noalign is no longer the first table token and compilation fails.  The
# column specification itself produces no visible content, so remove only
# that generated wrapper while retaining all cell-level change markup.
$diff = [System.IO.File]::ReadAllText($DiffTex)
$tabularRulePattern = '\\DIF(add|del)beginFL\s+(\\begin\{(?:tabular|tabularx)\}[^\r\n]*)\r?\n\s*\\DIF\1endFL\s+(\\(?:toprule|hline))'
$diff = [regex]::Replace(
    $diff,
    $tabularRulePattern,
    '$2' + [Environment]::NewLine + '$3'
)

# \multicolumn must be the first token in its cell.  Preserve the inner
# \DIFaddFL/\DIFdelFL text markup, but remove an outer FL wrapper that
# latexdiff may place before the command.
$multicolumnPattern = '\\DIF(add|del)beginFL\s+\\multicolumn([^\r\n]*?)\\DIF\1endFL(?=\s*\\\\)'
$diff = [regex]::Replace($diff, $multicolumnPattern, '\multicolumn$2')

# If an old ordinary cell is replaced by a new \multicolumn, latexdiff can
# leave the deleted cell before \multicolumn in the same alignment slot.
# Drop that obsolete header text and restore the required separator.
$deletedCellBeforeMulticolumnPattern = '\\DIFdelbeginFL\s+\\DIFdelFL\{[^{}]*\}\s*\\DIFdelendFL\s*(?=\\multicolumn)'
$diff = [regex]::Replace($diff, $deletedCellBeforeMulticolumnPattern, '& ')

# A simultaneous column-count and multicolumn-header change cannot be
# represented as an old and new row in one TeX alignment.  Render the new
# units row in blue; the old table body values remain visible in red below.
$changedUnitsRowPattern = '(?m)^\s*& \\DIFdelbeginFL %DIFDELCMD < & %%%\r?\n.*\r?\n.*\\multicolumn\{3\}.*\\\\\s*$'
$changedUnitsRow = '        & \DIFaddFL{[yr]} & & \multicolumn{3}{c}{\DIFaddFL{Amplitude }[\DIFaddFL{ph\,s$^{-1}$\,$\upmu$m$^{-1}$}]} \\'
$diff = [regex]::Replace($diff, $changedUnitsRowPattern, $changedUnitsRow)

# Cell text is already marked individually.  Remove a redundant outer wrapper
# spanning added/deleted rows when its end would precede a booktabs rule.
$diff = [regex]::Replace($diff, '(?m)^\\DIF(add|del)beginFL (?=\\DIF\1FL)', '')
$diff = [regex]::Replace($diff, '(?m)^\\DIF(add|del)endFL (?=\\bottomrule)', '')

# When the old revision has no bibliography, latexdiff can align deleted
# trailing prose with new \bibitem commands.  That puts list items inside
# \DIFaddbegin groups and makes thebibliography fail with "missing \item".
# Preserve every deleted prose block, then render the new bibliography as one
# blue structural addition without putting latexdiff groups around list items.
$newSource = [System.IO.File]::ReadAllText($NewTex)
$newBibliographyMatch = [regex]::Match(
    $newSource,
    '(?s)(\\clearpage\s*\\thispagestyle\{chapteropening\}\s*\\small\s*)?(\\begin\{thebibliography\}\{[^}]+\}.*?\\end\{thebibliography\})'
)

if ($newBibliographyMatch.Success) {
    $bibliographyIndex = $diff.IndexOf('\begin{thebibliography}', [System.StringComparison]::Ordinal)
    if ($bibliographyIndex -ge 0) {
        $regionStart = $diff.LastIndexOf(
            '\DIFaddbegin \clearpage',
            $bibliographyIndex,
            [System.StringComparison]::Ordinal
        )
        if ($regionStart -lt 0) {
            $regionStart = $bibliographyIndex
        }

        $bibliographyEndMarker = '\end{thebibliography}'
        $bibliographyEnd = $diff.IndexOf(
            $bibliographyEndMarker,
            $bibliographyIndex,
            [System.StringComparison]::Ordinal
        )

        if ($bibliographyEnd -ge 0) {
            $regionEnd = $bibliographyEnd + $bibliographyEndMarker.Length
            $outerAddEnd = $diff.IndexOf('\DIFaddend', $regionEnd, [System.StringComparison]::Ordinal)
            if ($outerAddEnd -ge 0) {
                $regionEnd = $outerAddEnd + '\DIFaddend'.Length
            }

            $generatedRegion = $diff.Substring($regionStart, $regionEnd - $regionStart)
            $deletedBlocks = @(
                [regex]::Matches($generatedRegion, '(?s)\\DIFdelbegin.*?\\DIFdelend') |
                    ForEach-Object { $_.Value }
            )
            $deletedPrefix = [string]::Join(
                [Environment]::NewLine + [Environment]::NewLine,
                $deletedBlocks
            )
            if ($deletedPrefix.Length -gt 0) {
                $deletedPrefix += [Environment]::NewLine + [Environment]::NewLine
            }

            $cleanPrefix = $newBibliographyMatch.Groups[1].Value
            $cleanBibliography = $newBibliographyMatch.Groups[2].Value
            $replacement = $deletedPrefix + $cleanPrefix +
                [Environment]::NewLine + '{\color{blue}' + [Environment]::NewLine +
                $cleanBibliography + [Environment]::NewLine + '}' +
                [Environment]::NewLine

            $diff = $diff.Substring(0, $regionStart) + $replacement + $diff.Substring($regionEnd)
        }
    }
}

[System.IO.File]::WriteAllText($DiffTex, $diff, [System.Text.UTF8Encoding]::new($false))

Push-Location $ThesisDir
try {
    pdflatex -interaction=nonstopmode -halt-on-error main_diff.tex | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "First pdflatex pass failed; see main_diff.log"
    }

    pdflatex -interaction=nonstopmode -halt-on-error main_diff.tex | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Second pdflatex pass failed; see main_diff.log"
    }
} finally {
    Pop-Location
}

Remove-Item $TmpDir -Recurse -Force

Write-Output "Diff PDF: $(Join-Path $ThesisDir 'main_diff.pdf')"
