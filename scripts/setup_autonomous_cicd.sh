#!/usr/bin/env bash
set -e

# Setup script for Autonomous CI/CD with Codegen SDK Integration

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🤖 Setting up Autonomous CI/CD System${NC}"
echo -e "${BLUE}This will configure intelligent, self-managing CI/CD pipelines${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Check if GitHub CLI is available
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️ GitHub CLI not found. Install from: https://cli.github.com/${NC}"
    echo -e "${BLUE}Continuing without GitHub CLI integration...${NC}"
    GH_AVAILABLE=false
else
    GH_AVAILABLE=true
    echo -e "${GREEN}✅ GitHub CLI found${NC}"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Create scripts directory if it doesn't exist
mkdir -p .github/scripts
echo -e "${GREEN}✅ Created .github/scripts directory${NC}"

# Make scripts executable
if [ -f ".github/scripts/autonomous_failure_analyzer.py" ]; then
    chmod +x .github/scripts/autonomous_failure_analyzer.py
    echo -e "${GREEN}✅ Made failure analyzer executable${NC}"
fi

if [ -f ".github/scripts/autonomous_dependency_manager.py" ]; then
    chmod +x .github/scripts/autonomous_dependency_manager.py
    echo -e "${GREEN}✅ Made dependency manager executable${NC}"
fi

if [ -f ".github/scripts/autonomous_performance_monitor.py" ]; then
    chmod +x .github/scripts/autonomous_performance_monitor.py
    echo -e "${GREEN}✅ Made performance monitor executable${NC}"
fi

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install --user codegen requests PyGithub safety pip-audit semantic-version 2>/dev/null || {
    echo -e "${YELLOW}⚠️ Some dependencies may need manual installation${NC}"
    echo -e "${BLUE}Required packages: codegen, requests, PyGithub, safety, pip-audit, semantic-version${NC}"
}

# Check for required secrets
echo ""
echo -e "${YELLOW}🔐 Checking GitHub Secrets Configuration${NC}"

MISSING_SECRETS=()

if [ "$GH_AVAILABLE" = true ]; then
    # Check if secrets exist using GitHub CLI
    if ! gh secret list | grep -q "CODEGEN_ORG_ID"; then
        MISSING_SECRETS+=("CODEGEN_ORG_ID")
    fi
    
    if ! gh secret list | grep -q "CODEGEN_TOKEN"; then
        MISSING_SECRETS+=("CODEGEN_TOKEN")
    fi
    
    if [ ${#MISSING_SECRETS[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All required secrets are configured${NC}"
    else
        echo -e "${YELLOW}⚠️ Missing secrets: ${MISSING_SECRETS[*]}${NC}"
    fi
else
    echo -e "${BLUE}ℹ️ Cannot check secrets without GitHub CLI${NC}"
    echo -e "${BLUE}Please ensure these secrets are set in your repository:${NC}"
    echo -e "  - CODEGEN_ORG_ID"
    echo -e "  - CODEGEN_TOKEN"
fi

# Create configuration template
echo ""
echo -e "${YELLOW}📝 Creating configuration template...${NC}"

cat > .github/autonomous-cicd-config.yml << 'EOF'
# Autonomous CI/CD Configuration
# Customize these settings for your project

# Failure Analysis Settings
failure_analysis:
  auto_fix_threshold: 0.7  # Confidence threshold for auto-fixes (0.0-1.0)
  max_auto_fixes_per_day: 5
  enable_learning: true

# Dependency Management Settings
dependency_management:
  update_strategy: "smart"  # Options: security-only, smart, all
  security_priority: "high"  # Options: low, medium, high
  test_before_merge: true
  auto_merge_patches: false

# Performance Monitoring Settings
performance_monitoring:
  regression_threshold: 20.0  # Percentage threshold for alerts
  auto_optimize: false  # Start with manual optimization
  baseline_days: 14  # Days of history for baseline calculation

# Notification Settings
notifications:
  create_issues: true
  slack_webhook: ""  # Optional Slack webhook URL
  email_alerts: false

# Safety Settings
safety:
  require_manual_approval:
    - major_dependency_updates
    - workflow_changes
    - security_fixes_above_threshold
  
  rollback_on_failure: true
  max_concurrent_optimizations: 1
EOF

echo -e "${GREEN}✅ Created configuration template: .github/autonomous-cicd-config.yml${NC}"

# Test the setup
echo ""
echo -e "${YELLOW}🧪 Testing setup...${NC}"

# Test Python imports
python3 -c "
try:
    import requests
    import json
    print('✅ Basic dependencies working')
except ImportError as e:
    print(f'⚠️ Import error: {e}')
" 2>/dev/null || echo -e "${YELLOW}⚠️ Some Python dependencies may need manual installation${NC}"

# Create a simple test script
cat > .github/scripts/test_autonomous_setup.py << 'EOF'
#!/usr/bin/env python3
"""Test script for autonomous CI/CD setup"""

import os
import sys

def test_environment():
    """Test if the environment is properly configured"""
    
    print("🧪 Testing Autonomous CI/CD Setup")
    print("=" * 40)
    
    # Check environment variables
    required_vars = ['CODEGEN_ORG_ID', 'CODEGEN_TOKEN', 'GITHUB_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("These are required for autonomous operations")
    else:
        print("✅ All required environment variables are set")
    
    # Test imports
    try:
        import requests
        import json
        from datetime import datetime
        print("✅ Core dependencies available")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test GitHub API access
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        try:
            import requests
            response = requests.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {github_token}'},
                timeout=10
            )
            if response.status_code == 200:
                print("✅ GitHub API access working")
            else:
                print(f"⚠️ GitHub API access issue: {response.status_code}")
        except Exception as e:
            print(f"⚠️ GitHub API test failed: {e}")
    
    print("\n🎉 Setup test completed!")
    return True

if __name__ == '__main__':
    test_environment()
EOF

chmod +x .github/scripts/test_autonomous_setup.py

# Final instructions
echo ""
echo -e "${GREEN}🎉 Autonomous CI/CD Setup Complete!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "1. ${YELLOW}Configure Secrets:${NC}"
echo -e "   - Go to your GitHub repository settings"
echo -e "   - Add secrets: CODEGEN_ORG_ID and CODEGEN_TOKEN"
echo -e "   - Get your Codegen credentials from: https://codegen.com"
echo ""
echo -e "2. ${YELLOW}Test the Setup:${NC}"
echo -e "   export GITHUB_TOKEN=your_token"
echo -e "   export CODEGEN_ORG_ID=your_org_id"
echo -e "   export CODEGEN_TOKEN=your_token"
echo -e "   python3 .github/scripts/test_autonomous_setup.py"
echo ""
echo -e "3. ${YELLOW}Customize Configuration:${NC}"
echo -e "   - Edit .github/autonomous-cicd-config.yml"
echo -e "   - Adjust thresholds and settings for your project"
echo ""
echo -e "4. ${YELLOW}Enable Autonomous Workflows:${NC}"
echo -e "   - Commit and push the new workflow files"
echo -e "   - The system will start monitoring automatically"
echo ""
echo -e "5. ${YELLOW}Monitor and Learn:${NC}"
echo -e "   - Check GitHub Issues for autonomous reports"
echo -e "   - Review auto-generated PRs"
echo -e "   - Adjust settings based on performance"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo -e "   - Read AUTONOMOUS_CICD.md for detailed information"
echo -e "   - Check .github/workflows/autonomous-ci.yml for workflow details"
echo ""
echo -e "${GREEN}Your CI/CD is now ready to become autonomous! 🤖${NC}"

