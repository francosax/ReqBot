# Version Management Guide

## 📌 How to Update the Version Number

ReqBot uses a **single source of truth** for version management to prevent inconsistencies across the codebase.

### ✅ The Right Way: Update `version.py` ONLY

When releasing a new version, **only update the `version.py` file**:

```python
# version.py

__version__ = "2.1.0"  # ← Update this
__version_info__ = (2, 1, 0)  # ← And this

# Version components
MAJOR = 2  # ← Update these
MINOR = 1
PATCH = 0

# Display version for GUI (automatically calculated)
GUI_VERSION = f"{MAJOR}.{MINOR}"  # Will be "2.1"

# Full version string
FULL_VERSION = __version__  # Will be "2.1.0"

# Version name (optional, for major releases)
VERSION_NAME = "Your Version Name"  # ← Update for major releases
```

### 🎯 What Gets Updated Automatically

Once you update `version.py`, these locations **automatically** use the correct version:

1. **GUI Window Title** (`main_app.py`)
   - Line 62: `self.setWindowTitle(f'RequirementBot {GUI_VERSION}')`
   - Displays: "RequirementBot 2.1"

2. **GUI Tests** (`test_gui.py`)
   - Line 34: `assert gui.windowTitle() == f"RequirementBot {GUI_VERSION}"`
   - Tests verify correct version is displayed

3. **Any Future Code**
   - Just import: `from version import GUI_VERSION, FULL_VERSION`
   - Use the variable instead of hardcoding

### ❌ What NOT to Do

**DON'T** hardcode version numbers in other files:

```python
# ❌ BAD - Don't do this
self.setWindowTitle('RequirementBot 2.1')  # Hardcoded!

# ✅ GOOD - Do this instead
from version import GUI_VERSION
self.setWindowTitle(f'RequirementBot {GUI_VERSION}')
```

---

## 🔢 Version Numbering Scheme

ReqBot follows **Semantic Versioning** (SemVer):

```
MAJOR.MINOR.PATCH
  2  .  1  .  0
```

### When to Increment:

- **MAJOR** (2.x.x → 3.0.0): Breaking changes, major rewrites
  - Example: Complete UI redesign, incompatible file formats

- **MINOR** (2.1.x → 2.2.0): New features, backward compatible
  - Example: Add OCR support, new export format

- **PATCH** (2.1.0 → 2.1.1): Bug fixes, minor improvements
  - Example: Fix a crash, improve error message

---

## 📋 Release Checklist

When releasing a new version, follow these steps:

### 1. Update Version Number
```python
# Edit version.py
MAJOR = 2
MINOR = 1
PATCH = 0
```

### 2. Run Tests
```bash
pytest -v
```
All 12 tests should pass.

### 3. Update Documentation

- [ ] Update `README.md` badge if needed:
  ```markdown
  [![Version](https://img.shields.io/badge/version-2.1.0-brightgreen.svg)](RELEASE_NOTES_v2.1.md)
  ```

- [ ] Create release notes: `RELEASE_NOTES_v2.1.md`

- [ ] Update `CLAUDE.md` if architecture changed

### 4. Commit Changes
```bash
git add version.py README.md RELEASE_NOTES_v2.1.md
git commit -m "Bump version to 2.1.0"
```

### 5. Create Git Tag
```bash
git tag -a v2.1.0 -m "Version 2.1.0 - [Brief Description]"
git push origin main
git push origin v2.1.0
```

### 6. Create GitHub Release
- Go to: `https://github.com/francosax/ReqBot/releases/new`
- Select tag: `v2.1.0`
- Add release notes
- Publish release

---

## 🛠️ Available Version Variables

Import from `version.py`:

```python
from version import (
    __version__,      # "2.0.0" - Full version string
    __version_info__, # (2, 0, 0) - Version tuple
    MAJOR,            # 2 - Major version number
    MINOR,            # 0 - Minor version number
    PATCH,            # 0 - Patch version number
    GUI_VERSION,      # "2.0" - For GUI display
    FULL_VERSION,     # "2.0.0" - Same as __version__
    VERSION_NAME      # "NLP Extraction Excellence" - Optional name
)
```

### Usage Examples:

**For GUI Display:**
```python
from version import GUI_VERSION
self.setWindowTitle(f'RequirementBot {GUI_VERSION}')
# Shows: "RequirementBot 2.0"
```

**For Logging:**
```python
from version import FULL_VERSION
logger.info(f"Starting ReqBot v{FULL_VERSION}")
# Logs: "Starting ReqBot v2.0.0"
```

**For About Dialog:**
```python
from version import FULL_VERSION, VERSION_NAME
about_text = f"ReqBot {FULL_VERSION}\n{VERSION_NAME}"
# Shows: "ReqBot 2.0.0\nNLP Extraction Excellence"
```

**For Comparisons:**
```python
from version import __version_info__, MAJOR, MINOR

if MAJOR >= 2:
    # Use new API
    pass

if __version_info__ >= (2, 1, 0):
    # Feature available in 2.1.0+
    pass
```

---

## 🔍 Verification

After updating the version, verify it's correct:

### Check GUI:
```bash
python main_app.py
```
Window title should show the correct version.

### Check Tests:
```bash
pytest test_gui.py::test_initial_state -v
```
Should pass with new version.

### Check Programmatically:
```bash
python -c "from version import FULL_VERSION; print(FULL_VERSION)"
```
Should print the new version.

---

## 🎯 Benefits of This Approach

✅ **Single Source of Truth**: One file to update
✅ **No Inconsistencies**: Version is always synchronized
✅ **Easy to Update**: Just edit `version.py`
✅ **Test Coverage**: Tests verify version is correct
✅ **Import Anywhere**: Any module can access version info
✅ **Semantic Versioning**: Clear, standard versioning scheme

---

## 📚 Additional Resources

- [Semantic Versioning](https://semver.org/)
- [Python Packaging Version Guide](https://packaging.python.org/en/latest/guides/single-sourcing-package-version/)
- [Git Tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging)

---

## 🆘 Troubleshooting

**Problem**: Tests fail after version update

**Solution**: Make sure you updated ALL three places in `version.py`:
```python
__version__ = "X.Y.Z"
__version_info__ = (X, Y, Z)
MAJOR = X
MINOR = Y
PATCH = Z
```

**Problem**: GUI shows wrong version

**Solution**: Check that `main_app.py` imports from `version.py`:
```python
from version import GUI_VERSION
```

**Problem**: Import error "No module named 'version'"

**Solution**: Make sure `version.py` is in the project root directory alongside `main_app.py`.

---

**Last Updated**: 2025-11-15
**Current Version**: 2.0.0
