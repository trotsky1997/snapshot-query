# PowerShell 发布脚本

Write-Host "🧹 清理旧的构建文件..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build, *.egg-info

Write-Host "📦 构建分发包..." -ForegroundColor Cyan
python -m build

Write-Host "✅ 检查分发包..." -ForegroundColor Cyan
twine check dist/*

Write-Host "📤 准备发布..." -ForegroundColor Green
Write-Host ""
Write-Host "方法 1: 使用 API Token (推荐，无需交互)" -ForegroundColor Cyan
Write-Host "  1. 在 https://pypi.org/manage/account/token/ 创建 API token" -ForegroundColor White
Write-Host "  2. 发布到 PyPI:" -ForegroundColor Yellow
Write-Host "     twine upload --username __token__ --password <your-token> dist/*" -ForegroundColor White
Write-Host "  3. 发布到 TestPyPI:" -ForegroundColor Yellow
Write-Host "     twine upload --repository testpypi --username __token__ --password <your-token> dist/*" -ForegroundColor White
Write-Host ""
Write-Host "方法 2: 使用用户名密码" -ForegroundColor Cyan
Write-Host "  twine upload --username <username> --password <password> dist/*" -ForegroundColor White
Write-Host ""
Write-Host "方法 3: 配置 .pypirc 后直接运行" -ForegroundColor Cyan
Write-Host "  twine upload dist/*" -ForegroundColor White
