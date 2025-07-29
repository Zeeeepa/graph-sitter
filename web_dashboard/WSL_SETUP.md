# WSL Setup Guide for Web Dashboard

This guide helps you set up the Web Dashboard in Windows Subsystem for Linux (WSL) environments, addressing common issues and providing optimal configuration.

## 🚀 Quick Start

For most users, the enhanced launch script will handle everything automatically:

```bash
# Development mode (recommended for first-time setup)
./launch_improved.sh --dev

# Full setup with WSL environment fixes
./launch_improved.sh --force-wsl-setup

# Production mode (after environment is configured)
./launch_improved.sh
```

## 🔧 Common WSL Issues and Solutions

### 1. Windows Node.js in WSL (UNC Path Errors)

**Problem**: You see errors like:
```
UNC paths are not supported. Defaulting to Windows directory.
Error: Cannot find module 'C:\Windows\install.js'
```

**Solution**: Install WSL-native Node.js:
```bash
# Automatic fix
./launch_improved.sh --force-wsl-setup

# Manual fix
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Docker Desktop Not Accessible

**Problem**: Docker commands fail with "daemon not accessible"

**Solutions**:

**Option A: Enable Docker Desktop WSL Integration**
1. Open Docker Desktop on Windows
2. Go to Settings → Resources → WSL Integration
3. Enable integration with your WSL distribution
4. Restart WSL: `wsl --shutdown` then reopen

**Option B: Install Docker Engine in WSL**
```bash
# Automatic installation
./launch_improved.sh --force-wsl-setup

# Manual installation
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker
```

### 3. npm Install Failures

**Problem**: npm packages fail to install with path-related errors

**Solution**: The enhanced script automatically:
- Cleans node_modules if path issues are detected
- Uses WSL-native Node.js
- Falls back to `--legacy-peer-deps` if needed

### 4. Backend Database Connection Issues

**Problem**: Backend fails with "No module named 'asyncpg'" or database errors

**Solution**: The script ensures:
- Virtual environment is properly activated
- All Python dependencies are installed
- Database connections are handled gracefully in dev mode

## 📋 Prerequisites

### Required Software
- WSL2 (recommended) or WSL1
- Python 3.8+ (usually pre-installed in WSL)
- Git (usually pre-installed in WSL)

### Optional Software
- Docker Desktop (for full functionality)
- Node.js 18+ (will be installed automatically if missing)

## 🛠️ Manual Setup (Advanced Users)

If you prefer to set up the environment manually:

### 1. Install WSL-Native Node.js
```bash
# Install Node.js 18.x LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

### 2. Set Up Python Environment
```bash
# Install Python dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
cd web_dashboard/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit with your actual values (or use dev values for testing)
nano .env
```

### 4. Start Services
```bash
# Backend (in backend directory with venv activated)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (in frontend directory)
npm install
npm run dev
```

## 🔍 Troubleshooting

### Environment Detection
Check your environment with:
```bash
./launch_improved.sh --verbose --dev
```

This will show:
- WSL version detection
- Node.js source (Windows vs WSL)
- Docker availability
- Environment variables status

### Common Error Messages

**"Windows Node.js detected in WSL"**
- Run with `--force-wsl-setup` to install WSL-native Node.js

**"Docker command found but daemon not accessible"**
- Enable Docker Desktop WSL integration or install Docker Engine

**"npm install failed"**
- Script will automatically retry with `--legacy-peer-deps`
- Check that you're using WSL-native Node.js

**"Backend server failed to start"**
- Check that virtual environment is activated
- Verify all Python dependencies are installed
- In dev mode, database errors are handled gracefully

### Path Issues
If you encounter path-related issues:

1. **Check current directory**: Ensure you're in the WSL file system (`/home/user/...`) not Windows (`/mnt/c/...`)
2. **Clean node_modules**: The script automatically cleans these if path issues are detected
3. **Use WSL-native tools**: Avoid mixing Windows and WSL executables

## 🎯 Best Practices

### Development Workflow
1. **Start with dev mode**: `./launch_improved.sh --dev`
2. **Fix environment issues**: Use `--force-wsl-setup` if needed
3. **Configure real APIs**: Edit `.env` file for production features
4. **Use full mode**: `./launch_improved.sh` for complete functionality

### Performance Tips
- Use WSL2 for better performance
- Store project files in WSL file system (not `/mnt/c/`)
- Enable Docker Desktop WSL integration for better Docker performance
- Use Windows Terminal for better WSL experience

### Security Considerations
- Keep `.env` file secure and never commit it
- Use development API keys for testing
- Configure real API keys only when needed

## 🆘 Getting Help

If you encounter issues not covered here:

1. **Run with verbose logging**: `./launch_improved.sh --verbose --dev`
2. **Check the logs**: Look for specific error messages
3. **Try force setup**: `./launch_improved.sh --force-wsl-setup`
4. **Clean restart**: Remove `node_modules`, `venv`, and `.env` then retry

### Environment Information
To report issues, include this information:
```bash
# WSL version
cat /proc/version

# Node.js location and version
which node && node --version

# Python version
python3 --version

# Docker status
docker --version && docker ps
```

## 📚 Additional Resources

- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Docker Desktop WSL Integration](https://docs.docker.com/desktop/windows/wsl/)
- [Node.js Installation Guide](https://nodejs.org/en/download/package-manager/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
