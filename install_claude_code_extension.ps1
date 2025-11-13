# PowerShell script to help install Claude Code extension in Cursor

Write-Host "Claude Code Extension Installation Helper" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Claude Code CLI is installed
Write-Host "Checking Claude Code CLI installation..." -ForegroundColor Yellow
try {
    $version = claude --version
    Write-Host "✓ Claude Code CLI is installed: $version" -ForegroundColor Green
} catch {
    Write-Host "✗ Claude Code CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "  npm install -g @anthropic-ai/claude-code" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Open Cursor IDE" -ForegroundColor White
Write-Host "2. Press Ctrl+Shift+X to open Extensions" -ForegroundColor White
Write-Host "3. Search for 'Claude Code' or 'Anthropic Claude Code'" -ForegroundColor White
Write-Host "4. Click Install" -ForegroundColor White
Write-Host ""
Write-Host "OR install manually from VSIX:" -ForegroundColor Cyan
Write-Host "1. Press Ctrl+Shift+P in Cursor" -ForegroundColor White
Write-Host "2. Type: 'Extensions: Install from VSIX...'" -ForegroundColor White
Write-Host "3. Download VSIX from: https://marketplace.visualstudio.com/items?itemName=Anthropic.claude-code" -ForegroundColor White
Write-Host ""
Write-Host "After installation, verify with:" -ForegroundColor Cyan
Write-Host "  claude /ide" -ForegroundColor Yellow



