# 🚀 Automated Development Workflow

This project uses **GitHub Actions** for automated version management and Docker image builds.

## 🎯 Developer Workflow

### **1. Feature Development**
```bash
# Create feature branch
git checkout -b feature/awesome-feature

# Develop your changes
# ... code, test, commit ...

# Push to remote
git push origin feature/awesome-feature
```

### **2. Create Pull Request**
1. **Create PR** from your feature branch to `main`
2. **Add version label** to indicate the type of change:
   - 🔧 **`patch`** - Bug fixes, documentation updates, small improvements
   - ✨ **`minor`** - New features, enhancements, non-breaking changes  
   - 💥 **`major`** - Breaking changes, major rewrites, API changes
   - 🤷 **No label** - Defaults to `patch` (safest option)

### **3. Merge & Automation**
- **Merge the PR** → Everything else happens automatically! 🤖

## 🤖 What Happens Automatically

### **After PR Merge:**

1. **🏷️ Auto-Version Workflow Triggers**
   - Detects the label type (`patch`, `minor`, `major`)
   - Bumps version in `pyproject.toml` 
   - Creates git commit: `"Bump version: 4.1.3 → 4.1.4"`
   - Creates git tag: `v4.1.4`
   - Pushes changes to main branch

2. **🐳 Docker Build Workflow Triggers**
   - Builds Docker image with new version
   - Creates multiple tags: `4.1.4`, `latest`, `v4.1.4`
   - Pushes to Docker Hub registry
   - Multi-platform support (if configured)

3. **📋 Summary Reports**
   - Detailed build summaries in GitHub Actions
   - Version change notifications
   - Docker image availability confirmation

## 📊 Version Management

### **Semantic Versioning (MAJOR.MINOR.PATCH):**
- **PATCH** (4.1.3 → 4.1.4): Bug fixes, small changes
- **MINOR** (4.1.3 → 4.2.0): New features, backward compatible
- **MAJOR** (4.1.3 → 5.0.0): Breaking changes, API changes

### **Single Source of Truth:**
All version information comes from `pyproject.toml`:
```toml
[project]
version = "4.1.3"  # This drives everything
```

## 🏷️ GitHub Labels Setup

### **Required Labels:**
Create these labels in your GitHub repository:

| Label | Color | Description | Version Bump |
|-------|-------|-------------|--------------|
| `patch` | 🔴 Red | Bug fixes and small improvements | X.Y.Z → X.Y.Z+1 |
| `minor` | 🔵 Blue | New features and enhancements | X.Y.Z → X.Y+1.0 |
| `major` | 🟣 Purple | Breaking changes | X.Y.Z → X+1.0.0 |

### **How to Create Labels:**
1. Go to repository → **Issues** → **Labels**
2. Click **"New label"** for each label above
3. Copy the name, choose the color, add description

## 🐳 Docker Integration

### **Automatic Docker Builds:**
- **Trigger**: Version tags (when auto-versioning creates them)
- **Registry**: Docker Hub (configurable)
- **Tags Created**:
  - `repository:4.1.4` (specific version)
  - `repository:latest` (always points to newest)
  - `repository:v4.1.4` (with 'v' prefix)

### **Manual Docker Build:**
If needed, you can manually trigger Docker builds:
1. Go to **Actions** tab
2. Select **"Build and Push Docker Image"**
3. Click **"Run workflow"**
4. Choose branch and click **"Run workflow"**

## 🔧 Configuration

### **Required GitHub Secrets:**
- `DOCKERHUB_USERNAME` - Your Docker Hub username
- `DOCKERHUB_TOKEN` - Your Docker Hub access token

### **Repository Settings:**
- **Actions enabled** - Required for automation
- **Branch protection** (optional but recommended)
- **Required status checks** for PR merging

## 🎭 Example Scenarios

### **Bug Fix Release:**
```bash
git checkout -b fix/memory-leak
# ... fix the bug ...
git push origin fix/memory-leak
```
- Create PR with 🔧 **`patch`** label  
- Merge → `4.1.3` becomes `4.1.4`

### **New Feature Release:**
```bash
git checkout -b feature/notifications
# ... add new feature ...
git push origin feature/notifications
```
- Create PR with ✨ **`minor`** label
- Merge → `4.1.3` becomes `4.2.0`

### **Breaking Change Release:**
```bash
git checkout -b breaking/api-v2
# ... breaking changes ...
git push origin breaking/api-v2
```
- Create PR with 💥 **`major`** label
- Merge → `4.1.3` becomes `5.0.0`

## ✅ Benefits

- 🚫 **No manual version management** - Everything automated
- 🛡️ **Consistent versioning** - No human errors
- 📦 **Automatic releases** - Docker images always up-to-date
- 📋 **Clear history** - Git tags track all releases
- 🚀 **Fast deployment** - Version → Docker image in minutes
- 🔄 **Rollback friendly** - Each version tagged and available

## 🐛 Troubleshooting

### **Action Failed:**
1. Check **Actions** tab for error details
2. Common issues:
   - Missing or invalid Docker Hub credentials
   - Label not found (defaults to `patch`)
   - Version format errors in `pyproject.toml`

### **No Docker Build:**
- Docker builds **only trigger on version tags**
- Check if auto-versioning workflow completed successfully
- Manual trigger available if needed

### **Version Didn't Bump:**
- Check if PR had the correct label
- Verify auto-versioning workflow ran successfully
- Check repository permissions for bot commits

---

**🎉 Happy coding!** This workflow handles all the tedious release management so you can focus on building great features.
