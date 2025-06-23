#!/usr/bin/env python3
"""
HyperLiquid AI Trading Bot - System Health Check
Comprehensive system diagnosis and status report
"""

import requests
import subprocess
import sys
import json
import time
from pathlib import Path
import socket

class HealthChecker:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.checks = []
        self.errors = []
        self.warnings = []
        
    def print_banner(self):
        """Print health check banner"""
        print("🏥 HyperLiquid AI Trading Bot - System Health Check")
        print("=" * 60)
        print("📁 Project Directory:", self.root_dir)
        print("⏰ Check Time:", time.strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)
        
    def check_files_structure(self):
        """Check if all required files exist"""
        print("\n📁 File Structure Check")
        print("-" * 30)
        
        required_files = [
            "main.py",
            "requirements.txt",
            ".env.example",
            "dashboard/backend/app.py",
            "dashboard/frontend/package.json",
            "dashboard/start_server.py",
            "scripts/start_all.py"
        ]
        
        for file_path in required_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path} - MISSING")
                self.errors.append(f"Missing file: {file_path}")
                
    def check_python_dependencies(self):
        """Check Python environment and dependencies"""
        print("\n🐍 Python Environment Check")
        print("-" * 30)
        
        # Python version
        python_version = sys.version.split()[0]
        print(f"🐍 Python Version: {python_version}")
        
        if sys.version_info < (3, 10):
            self.errors.append("Python 3.10+ required")
            print("❌ Python 3.10+ required")
        else:
            print("✅ Python version OK")
            
        # Check if requirements.txt exists and try to import key modules
        req_file = self.root_dir / "requirements.txt"
        if req_file.exists():
            print("✅ requirements.txt found")
            
            # Try importing key modules
            key_modules = [
                ("fastapi", "FastAPI"),
                ("uvicorn", "Uvicorn"),
                ("websockets", "WebSockets"),
                ("sqlite3", "SQLite3"),
                ("requests", "Requests")
            ]
            
            for module, name in key_modules:
                try:
                    __import__(module)
                    print(f"✅ {name} available")
                except ImportError:
                    print(f"⚠️ {name} not installed")
                    self.warnings.append(f"Module {name} not available")
        else:
            print("❌ requirements.txt not found")
            self.errors.append("requirements.txt missing")
            
    def check_nodejs_environment(self):
        """Check Node.js and npm environment"""
        print("\n📦 Node.js Environment Check")
        print("-" * 30)
        
        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], 
                                  capture_output=True, text=True, check=True)
            node_version = result.stdout.strip()
            print(f"✅ Node.js: {node_version}")
            
            # Check if version is 18+
            version_num = int(node_version.replace('v', '').split('.')[0])
            if version_num < 18:
                self.warnings.append("Node.js 18+ recommended")
                print("⚠️ Node.js 18+ recommended")
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Node.js not found")
            self.errors.append("Node.js not installed")
            
        # Check npm
        try:
            result = subprocess.run(["npm", "--version"], 
                                  capture_output=True, text=True, check=True)
            npm_version = result.stdout.strip()
            print(f"✅ npm: {npm_version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ npm not found")
            self.errors.append("npm not installed")
            
        # Check frontend dependencies
        frontend_dir = self.root_dir / "dashboard" / "frontend"
        if (frontend_dir / "node_modules").exists():
            print("✅ Frontend dependencies installed")
        else:
            print("⚠️ Frontend dependencies not installed")
            self.warnings.append("Run 'npm install' in dashboard/frontend")
            
    def check_ports_availability(self):
        """Check if required ports are available"""
        print("\n🔌 Port Availability Check")
        print("-" * 30)
        
        ports_to_check = [
            (8000, "Dashboard Backend"),
            (5173, "Frontend Dev Server"),
            (3000, "Alternative Frontend")
        ]
        
        for port, service in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"⚠️ Port {port} ({service}) - IN USE")
                self.warnings.append(f"Port {port} already in use")
            else:
                print(f"✅ Port {port} ({service}) - Available")
                
    def check_dashboard_backend_status(self):
        """Check if dashboard backend is running"""
        print("\n⚙️ Dashboard Backend Status")
        print("-" * 30)
        
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Dashboard Backend - RUNNING")
                print(f"   Status: {data.get('status', 'unknown')}")
                
                services = data.get('services', {})
                for service, status in services.items():
                    if status == 'operational':
                        print(f"   ✅ {service}")
                    else:
                        print(f"   ❌ {service}")
                        
            else:
                print(f"⚠️ Dashboard Backend - HTTP {response.status_code}")
                self.warnings.append("Dashboard backend responding with errors")
                
        except requests.exceptions.ConnectionError:
            print("❌ Dashboard Backend - NOT RUNNING")
        except requests.exceptions.RequestException as e:
            print(f"❌ Dashboard Backend - ERROR: {e}")
            self.errors.append(f"Backend error: {e}")
            
    def check_database_status(self):
        """Check database file and accessibility"""
        print("\n🗄️ Database Status")
        print("-" * 30)
        
        db_file = self.root_dir / "trades.db"
        if db_file.exists():
            print(f"✅ Database file exists ({db_file.stat().st_size} bytes)")
            
            # Try to connect to database
            try:
                import sqlite3
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                print(f"✅ Database accessible ({len(tables)} tables)")
                for table in tables:
                    print(f"   📋 Table: {table[0]}")
                    
            except Exception as e:
                print(f"❌ Database connection error: {e}")
                self.errors.append(f"Database error: {e}")
        else:
            print("⚠️ Database file not found (will be created on first run)")
            self.warnings.append("Database will be created when bot runs")
            
    def check_environment_config(self):
        """Check environment configuration"""
        print("\n⚙️ Environment Configuration")
        print("-" * 30)
        
        env_file = self.root_dir / ".env"
        env_example = self.root_dir / ".env.example"
        
        if env_example.exists():
            print("✅ .env.example found")
        else:
            print("❌ .env.example missing")
            self.errors.append(".env.example file missing")
            
        if env_file.exists():
            print("✅ .env configuration found")
            
            # Check for critical variables
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read()
                    
                critical_vars = [
                    "HL_SECRET_KEY",
                    "ALLORA_UPSHOT_KEY"
                ]
                
                for var in critical_vars:
                    if var in env_content:
                        if f"{var}=your_" not in env_content:
                            print(f"✅ {var} configured")
                        else:
                            print(f"⚠️ {var} needs configuration")
                            self.warnings.append(f"{var} not properly configured")
                    else:
                        print(f"❌ {var} missing")
                        self.errors.append(f"Missing environment variable: {var}")
                        
            except Exception as e:
                print(f"❌ Error reading .env: {e}")
                self.errors.append(f"Environment file error: {e}")
        else:
            print("❌ .env configuration missing")
            self.errors.append("Create .env file from .env.example")
            
    def generate_summary(self):
        """Generate health check summary"""
        print("\n" + "="*60)
        print("📊 HEALTH CHECK SUMMARY")
        print("="*60)
        
        total_checks = len(self.checks)
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        
        if error_count == 0 and warning_count == 0:
            print("🎉 SYSTEM HEALTHY - All checks passed!")
            status = "HEALTHY"
        elif error_count == 0:
            print(f"⚠️ SYSTEM OK - {warning_count} warnings found")
            status = "OK_WITH_WARNINGS"
        else:
            print(f"❌ SYSTEM ISSUES - {error_count} errors, {warning_count} warnings")
            status = "ISSUES_FOUND"
            
        print(f"\n📈 Check Results:")
        print(f"   Errors: {error_count}")
        print(f"   Warnings: {warning_count}")
        
        if self.errors:
            print(f"\n❌ ERRORS TO FIX:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
                
        if self.warnings:
            print(f"\n⚠️ WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
                
        print(f"\n🚀 RECOMMENDED ACTIONS:")
        if error_count > 0:
            print("   1. Fix all errors listed above")
            print("   2. Run health check again")
        elif warning_count > 0:
            print("   1. Review warnings (optional)")
            print("   2. System ready to run")
        else:
            print("   1. System ready - run 'python scripts/start_all.py'")
            
        return status
        
    def run(self):
        """Execute all health checks"""
        self.print_banner()
        
        # Run all checks
        self.check_files_structure()
        self.check_python_dependencies()
        self.check_nodejs_environment()
        self.check_ports_availability()
        self.check_dashboard_backend_status()
        self.check_database_status()
        self.check_environment_config()
        
        # Generate summary
        status = self.generate_summary()
        
        return status == "HEALTHY"

if __name__ == "__main__":
    checker = HealthChecker()
    try:
        is_healthy = checker.run()
        sys.exit(0 if is_healthy else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Health check cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Health check error: {e}")
        sys.exit(1) 