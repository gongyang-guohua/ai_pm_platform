
# 临时将 Node.js 添加到 PATH
$env:PATH = "C:\Program Files\nodejs;" + $env:PATH

# 检查依赖并运行
Write-Host "Checking Node.js version..."
node -v
Write-Host "Running npm run dev..."
npm run dev
