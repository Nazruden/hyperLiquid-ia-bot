#!/usr/bin/env python3
"""
HyperLiquid AI Trading Bot - TESTNET Deployment Script
Automated deployment and validation for testnet environment
"""

import os
import sys
import time
import json
import shutil
import subprocess
import requests
from pathlib import Path
from datetime import datetime

class TestnetDeployer:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.config_file = self.root_dir / ".env.testnet"
        self.log_dir = self.root_dir / "logs"
        self.backup_dir = self.root_dir / "backups" / f"testnet_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.errors = []
        self.warnings = []
        
        # Create necessary directories
        self.log_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def print_banner(self):
        """Print deployment banner"""
        print("🚀 HyperLiquid AI Trading Bot - TESTNET DEPLOYMENT")
        print("=" * 60)
        print(f"📁 Project Directory: {self.root_dir}")
        print(f"⏰ Deployment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Configuration: {self.config_file}")
        print(f"📦 Backup Directory: {self.backup_dir}")
        print("=" * 60)
        
    def step(self, message):
        """Print step with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] 🔄 {message}")
        
    def success(self, message):
        """Print success message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ {message}")
        
    def warning(self, message):
        """Print warning message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ⚠️ {message}")
        self.warnings.append(message)
        
    def error(self, message):
        """Print error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ {message}")
        self.errors.append(message)
        
    def backup_current_config(self):
        """Backup current configuration"""
        self.step("Backing up current configuration")
        
        files_to_backup = [".env", "trades.db", "memory-bank/"]
        
        for file_path in files_to_backup:
            source = self.root_dir / file_path
            if source.exists():
                if source.is_file():
                    destination = self.backup_dir / file_path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
                    self.success(f"Backed up: {file_path}")
                elif source.is_dir():
                    destination = self.backup_dir / file_path
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                    self.success(f"Backed up directory: {file_path}")
            else:
                self.warning(f"File not found for backup: {file_path}")
                
    def validate_testnet_config(self):
        """Validate testnet configuration file"""
        self.step("Validating testnet configuration")
        
        if not self.config_file.exists():
            self.error(f"Testnet config file not found: {self.config_file}")
            return False
            
        # Read configuration with UTF-8 encoding
        config_content = self.config_file.read_text(encoding='utf-8')
        
        # Check critical settings
        required_settings = [
            ("MAINNET=False", "TESTNET mode must be enabled"),
            ("HL_SECRET_KEY=", "HyperLiquid secret key must be set"),
            ("ALLORA_UPSHOT_KEY=", "AlloraNetwork API key must be set"),
            ("VALIDATION_SCORE_THRESHOLD=", "Validation threshold must be configured"),
            ("LAG_DETECTION_ENABLED=True", "Lag detection must be enabled"),
            ("ADAPTIVE_THRESHOLDS=True", "Adaptive thresholds must be enabled")
        ]
        
        for setting, description in required_settings:
            if setting.split('=')[0] + "=" in config_content:
                if setting in config_content:
                    self.success(f"✓ {description}")
                else:
                    if setting.startswith("MAINNET=False"):
                        self.error(f"CRITICAL: {description}")
                        return False
                    else:
                        self.warning(f"Check required: {description}")
            else:
                self.warning(f"Setting not found: {setting.split('=')[0]}")
                
        return True
        
    def run_comprehensive_tests(self):
        """Run all unit tests before deployment"""
        self.step("Running comprehensive test suite")
        
        try:
            # Run all tests
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.success("All tests passed ✅")
                
                # Count tests
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if "passed" in line and "test" in line:
                        self.success(f"Test Results: {line.strip()}")
                        break
                        
                return True
            else:
                self.error("Some tests failed")
                print("\nTest Output:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except FileNotFoundError:
            self.error("pytest not found. Install with: pip install pytest")
            return False
        except Exception as e:
            self.error(f"Test execution failed: {e}")
            return False
            
    def setup_testnet_environment(self):
        """Setup testnet environment"""
        self.step("Setting up testnet environment")
        
        # Copy testnet config to main .env with proper encoding
        if self.config_file.exists():
            env_file = self.root_dir / ".env"
            # Read with UTF-8 and write with UTF-8 to ensure proper encoding
            config_content = self.config_file.read_text(encoding='utf-8')
            env_file.write_text(config_content, encoding='utf-8')
            self.success("Testnet configuration activated")
        else:
            self.error("Testnet configuration file not found")
            return False
            
        # Create testnet-specific database
        testnet_db = self.root_dir / "testnet_trades.db"
        if not testnet_db.exists():
            # Initialize empty database
            try:
                import sqlite3
                conn = sqlite3.connect(testnet_db)
                conn.close()
                self.success("Testnet database initialized")
            except Exception as e:
                self.error(f"Failed to initialize testnet database: {e}")
                return False
        else:
            self.success("Testnet database already exists")
            
        # Create logs directory with proper permissions
        testnet_logs = self.log_dir / "testnet"
        testnet_logs.mkdir(exist_ok=True)
        self.success("Testnet logs directory prepared")
        
        return True
        
    def validate_api_connectivity(self):
        """Test API connectivity for all services"""
        self.step("Validating API connectivity")
        
        # Test HyperLiquid testnet endpoint
        try:
            response = requests.get(
                "https://api.hyperliquid-testnet.xyz",
                timeout=10,
                headers={"User-Agent": "HyperLiquid-AI-Bot/1.0"}
            )
            if response.status_code < 500:
                self.success("HyperLiquid testnet API reachable")
            else:
                self.warning(f"HyperLiquid API response: {response.status_code}")
        except Exception as e:
            self.error(f"HyperLiquid testnet API unreachable: {e}")
            
        # Test AlloraNetwork API
        try:
            response = requests.get(
                "https://api.allora.network/v2/allora/consumer/",
                timeout=10,
                headers={"User-Agent": "HyperLiquid-AI-Bot/1.0"}
            )
            if response.status_code < 500:
                self.success("AlloraNetwork API reachable")
            else:
                self.warning(f"AlloraNetwork API response: {response.status_code}")
        except Exception as e:
            self.warning(f"AlloraNetwork API check failed: {e}")
            
    def perform_dry_run(self):
        """Perform dry run validation"""
        self.step("Performing dry run validation")
        
        try:
            # Import and test core modules
            sys.path.append(str(self.root_dir))
            
            # Test configuration loading
            from utils.env_loader import EnvLoader
            env_loader = EnvLoader()
            config = env_loader.get_config()
            
            # Validate critical configuration
            if config.get('mainnet') == 'False':
                self.success("✓ Testnet mode confirmed")
            else:
                self.error("❌ CRITICAL: Not in testnet mode!")
                return False
                
            # Test AI services initialization
            if config.get('allora_upshot_key'):
                self.success("✓ AlloraNetwork API key configured")
            else:
                self.error("❌ AlloraNetwork API key missing")
                return False
                
            # Test validation system
            validation_threshold = config.get('validation_score_threshold', 0)
            if 0.3 <= validation_threshold <= 0.8:
                self.success(f"✓ Validation threshold: {validation_threshold}")
            else:
                self.warning(f"⚠️ Validation threshold unusual: {validation_threshold}")
                
            # Test adaptive thresholds
            if config.get('adaptive_thresholds'):
                self.success("✓ Adaptive thresholds enabled")
            else:
                self.warning("⚠️ Adaptive thresholds disabled")
                
            # Test lag detection
            lag_enabled = config.get('lag_detection_enabled', False)
            if lag_enabled:
                self.success("✓ Lag detection enabled")
            else:
                self.warning("⚠️ Lag detection disabled")
                
            return True
            
        except Exception as e:
            self.error(f"Dry run failed: {e}")
            return False
            
    def start_testnet_deployment(self):
        """Start the testnet bot deployment"""
        self.step("Initiating testnet bot deployment")
        
        try:
            # Start the dashboard backend first
            self.step("Starting dashboard backend")
            
            dashboard_cmd = [
                sys.executable, 
                "dashboard/start_server.py"
            ]
            
            # Start in background
            process = subprocess.Popen(
                dashboard_cmd,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it time to start
            time.sleep(5)
            
            # Check if backend is running
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    self.success("Dashboard backend started successfully")
                else:
                    self.warning(f"Dashboard backend responding with status: {response.status_code}")
            except:
                self.warning("Dashboard backend may not be fully ready")
                
            self.success("Testnet deployment initiated")
            self.success("🎯 Dashboard: http://localhost:8000")
            self.success("🎯 Frontend: http://localhost:5173")
            
            return True
            
        except Exception as e:
            self.error(f"Failed to start testnet deployment: {e}")
            return False
            
    def generate_deployment_report(self):
        """Generate deployment summary report"""
        self.step("Generating deployment report")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "deployment_type": "testnet",
            "status": "success" if len(self.errors) == 0 else "warning" if len(self.warnings) > 0 else "failed",
            "errors": self.errors,
            "warnings": self.warnings,
            "config_file": str(self.config_file),
            "backup_location": str(self.backup_dir)
        }
        
        # Save report
        report_file = self.backup_dir / "deployment_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TESTNET DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        if len(self.errors) == 0:
            print("✅ DEPLOYMENT SUCCESSFUL")
        elif len(self.warnings) > 0:
            print("⚠️ DEPLOYMENT COMPLETED WITH WARNINGS")
        else:
            print("❌ DEPLOYMENT FAILED")
            
        print(f"\nErrors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"   - {error}")
                
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"   - {warning}")
                
        print(f"\n📋 Full report saved: {report_file}")
        
        if len(self.errors) == 0:
            print("\n🚀 NEXT STEPS:")
            print("1. Launch complete orchestrator: python scripts/testnet_orchestrator.py")
            print("2. OR manually start services:")
            print("   - Dashboard: python dashboard/start_server.py")
            print("   - Frontend: cd dashboard/frontend && npm run dev")
            print("   - Bot: python main.py")
            print("3. Monitor dashboard: http://localhost:8000")
            print("4. Validate AI predictions working")
            print("5. Watch for 1 hour minimum before leaving unattended")
            print("\n⚡ RECOMMENDED: Use the orchestrator for full control!")
            print("   python scripts/testnet_orchestrator.py")
            
        return len(self.errors) == 0
        
    def deploy(self):
        """Execute complete testnet deployment"""
        self.print_banner()
        
        # Step 1: Backup
        self.backup_current_config()
        
        # Step 2: Validate configuration
        if not self.validate_testnet_config():
            self.error("Configuration validation failed")
            return False
            
        # Step 3: Run tests
        if not self.run_comprehensive_tests():
            self.error("Test suite failed - deployment aborted")
            return False
            
        # Step 4: Setup environment
        if not self.setup_testnet_environment():
            self.error("Environment setup failed")
            return False
            
        # Step 5: API connectivity
        self.validate_api_connectivity()
        
        # Step 6: Dry run
        if not self.perform_dry_run():
            self.error("Dry run validation failed")
            return False
            
        # Step 7: Deploy
        if not self.start_testnet_deployment():
            self.error("Deployment start failed")
            return False
            
        # Step 8: Generate report
        return self.generate_deployment_report()


def main():
    """Main deployment function"""
    deployer = TestnetDeployer()
    
    try:
        success = deployer.deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Deployment failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 