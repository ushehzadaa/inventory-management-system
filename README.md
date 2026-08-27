# Integrator Inventory Pro

Professional Inventory Management System designed for an MSc DevOps portfolio.

## Features
- Secure admin login
- KPI dashboard
- Product/SKU/category/supplier management
- Stock IN/OUT/ADJUST movements
- Low-stock alerts and reorder levels
- Inventory valuation
- Search/filter and CSV export
- Audit log
- Health API for CI/CD and Kubernetes probes
- Docker, Jenkins, Kubernetes and cPanel/Passenger ready

## Demo Login
Email: `admin@integratortool.com`  
Password: `Admin@123`

## Local Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`

## Docker
```bash
docker build -t integrator-inventory:v1 .
docker run -d --name integrator-inventory -p 5000:5000 integrator-inventory:v1
```

## Viva Demo Change
Create a branch such as `feature/critical-stock-alert`, change the visible dashboard label **Low Stock** to **Critical Stock**, push the branch, create/merge a PR, and let Jenkins build/deploy the new image.

Rollback options:
- Git: `git revert <commit>`
- Docker: redeploy a previous image tag
- Kubernetes: `kubectl rollout undo deployment/integrator-inventory`

## cPanel Deployment
If cPanel provides **Setup Python App**:
1. Upload/extract the project.
2. Create Python 3.11/3.12 app.
3. Startup file: `passenger_wsgi.py`
4. Entry point: `application`
5. Install `requirements.txt`.
6. Add environment variables `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.
7. Restart the Python application.

Use cPanel as a public demonstration copy. Keep the assessed CI/CD path on AWS EC2/Jenkins/Docker/Kubernetes.
