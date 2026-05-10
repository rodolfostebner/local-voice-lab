param (
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$sessionsDir = Join-Path $workspaceRoot "output\sessions"

if (-Not (Test-Path $sessionsDir)) {
    Write-Host "[!] Diretório de sessões não encontrado: $sessionsDir" -ForegroundColor Yellow
    exit
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " LAB VOZ LOCAL — SESSIONS CLEANUP" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "[MODO DRY-RUN] Nenhuma alteração real será feita." -ForegroundColor Yellow
}

$now = Get-Date
$limitActive = $now.AddHours(-2)
$limitWavs = $now.AddDays(-7)
$limitDeep = $now.AddDays(-30)
$maxSessions = 200

$freedBytes = 0
$deletedWavs = 0
$deletedSessions = 0

$sessions = Get-ChildItem -Path $sessionsDir -Directory | Sort-Object CreationTime

Write-Host "Total de Sessões Analisadas: $($sessions.Count)"

# 1. Enforce Max Sessions (Manter apenas as 200 mais recentes)
if ($sessions.Count -gt $maxSessions) {
    $overflowCount = $sessions.Count - $maxSessions
    Write-Host "[!] Limite de $maxSessions sessões excedido. Removendo $overflowCount sessões antigas..." -ForegroundColor Yellow
    
    $sessionsToDelete = $sessions | Select-Object -First $overflowCount
    foreach ($session in $sessionsToDelete) {
        $size = (Get-ChildItem $session.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $freedBytes += $size
        $deletedSessions++
        
        if ($DryRun) {
            Write-Host "  [DRY-RUN] Deletar sessão inteira: $($session.Name) ($([math]::Round($size/1MB, 2)) MB)" -ForegroundColor Gray
        } else {
            Remove-Item -Path $session.FullName -Recurse -Force
        }
    }
    
    # Atualiza lista de sessões restantes
    $sessions = Get-ChildItem -Path $sessionsDir -Directory | Sort-Object CreationTime
}

# 2. Varredura por Retenção de Tempo
foreach ($session in $sessions) {
    # Ignora sessões ativas (menos de 2h)
    if ($session.CreationTime -gt $limitActive) {
        continue
    }

    # Deep Cleanup: Remoção total se mais velha que 30 dias
    if ($session.CreationTime -lt $limitDeep) {
        $size = (Get-ChildItem $session.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $freedBytes += $size
        $deletedSessions++
        
        if ($DryRun) {
            Write-Host "  [DRY-RUN] Deletar sessão inteira (>30 dias): $($session.Name)" -ForegroundColor Gray
        } else {
            Remove-Item -Path $session.FullName -Recurse -Force
        }
        continue
    }

    # Cleanup Soft: Remove apenas WAVs antigos (>7 dias)
    if ($session.CreationTime -lt $limitWavs) {
        $wavFiles = Get-ChildItem -Path $session.FullName -Filter "*.wav" -Recurse -File
        foreach ($wav in $wavFiles) {
            $freedBytes += $wav.Length
            $deletedWavs++
            
            if ($DryRun) {
                Write-Host "  [DRY-RUN] Deletar WAV (>7 dias): $($wav.FullName)" -ForegroundColor Gray
            } else {
                Remove-Item -Path $wav.FullName -Force
            }
        }
        
        # Cleanup Soft: Remove temporários de conversão (webm)
        $webmFiles = Get-ChildItem -Path $session.FullName -Filter "*.webm" -Recurse -File
        foreach ($webm in $webmFiles) {
            $freedBytes += $webm.Length
            if (-Not $DryRun) {
                Remove-Item -Path $webm.FullName -Force
            }
        }
    }
}

Write-Host "------------------------------------------" -ForegroundColor Cyan
Write-Host "Resumo da Limpeza:"
Write-Host " - Sessões Removidas: $deletedSessions"
Write-Host " - WAVs Removidos:    $deletedWavs"
Write-Host " - Espaço Liberado:   $([math]::Round($freedBytes / 1MB, 2)) MB"
Write-Host "==========================================" -ForegroundColor Cyan
