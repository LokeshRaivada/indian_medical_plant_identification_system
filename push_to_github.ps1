Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Pushing Indian Medicinal Plant AI Project to GitHub" -ForegroundColor Green
Write-Host "Repository: https://github.com/LokeshRaivada/indian_medical_plant_identification.git" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan

$env:Path += ";C:\Users\GMRIT\AppData\Local\Programs\Git\cmd"
& "C:\Users\GMRIT\AppData\Local\Programs\Git\cmd\git.exe" push -u origin main
