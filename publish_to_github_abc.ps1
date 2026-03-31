# GitHub에 레포지토리 "abc"를 만들고 현재 브랜치를 push 합니다.
# 사전 준비 (택 1):
#   A) 터미널에서: gh auth login
#   B) Fine-grained 또는 classic PAT를 환경변수로: $env:GH_TOKEN = "ghp_...."

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Ensure-GhAuth {
    cmd /c "gh auth status >nul 2>&1"
    if ($LASTEXITCODE -eq 0) { return }

    if ($env:GH_TOKEN -or $env:GITHUB_TOKEN) {
        $t = if ($env:GH_TOKEN) { $env:GH_TOKEN } else { $env:GITHUB_TOKEN }
        $t | gh auth login --hostname github.com --git-protocol https --with-token
        return
    }

    Write-Host ""
    Write-Host "GitHub CLI에 로그인되어 있지 않습니다." -ForegroundColor Yellow
    Write-Host "다음 중 하나를 실행한 뒤 이 스크립트를 다시 실행하세요." -ForegroundColor Yellow
    Write-Host "  gh auth login" -ForegroundColor Cyan
    Write-Host "또는 PAT를 설정한 뒤:" -ForegroundColor Yellow
    Write-Host '  $env:GH_TOKEN = "여기에_토큰"' -ForegroundColor Cyan
    Write-Host "  .\publish_to_github_abc.ps1" -ForegroundColor Cyan
    exit 1
}

Ensure-GhAuth

$hasOrigin = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "원격 저장소가 없습니다. gh로 레포 abc를 생성하고 push합니다..." -ForegroundColor Green
    gh repo create abc --public --source=. --remote=origin --push
} else {
    Write-Host "origin이 이미 있습니다. push만 수행합니다..." -ForegroundColor Green
    git push -u origin main
}

Write-Host "완료. 저장소 확인: gh repo view --web" -ForegroundColor Green
