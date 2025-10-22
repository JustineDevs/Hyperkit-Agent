# 🔒 Security Scan Report
**Scan Date:** 2025-10-22 16:06:52
**Total Issues:** 13

## 📊 Summary
- 🚨 **Critical:** 1
- ⚠️ **High:** 0
- ℹ️ **Medium:** 12

## 🚨 Critical Issues
### tests\conftest.py:100
- **Type:** private_key
- **Description:** Private key detected
- **Pattern:** `0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef`
- **Fix:** Use environment variable: PRIVATE_KEY

## ℹ️ Medium Priority Issues
### ENVIRONMENT_SETUP.md:11
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_google_api_key_here`
- **Fix:** Use environment variable

### ENVIRONMENT_SETUP.md:14
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_openai_api_key_here`
- **Fix:** Use environment variable

### ENVIRONMENT_SETUP.md:52
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_obsidian_api_key_here`
- **Fix:** Use environment variable

### ENVIRONMENT_SETUP.md:113
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_google_api_key_here`
- **Fix:** Use environment variable

### ENVIRONMENT_SETUP.md:114
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_openai_api_key_here`
- **Fix:** Use environment variable

### ENVIRONMENT_SETUP.md:119
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_obsidian_api_key_here`
- **Fix:** Use environment variable

### ENVIRONMENT_SETUP.md:128
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_langsmith_api_key_here`
- **Fix:** Use environment variable

### setup.py:147
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_obsidian_api_key_here`
- **Fix:** Use environment variable

### setup.py:378
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_google_api_key_here`
- **Fix:** Use environment variable

### setup.py:379
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_openai_api_key_here`
- **Fix:** Use environment variable

### setup.py:384
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your_obsidian_api_key_here`
- **Fix:** Use environment variable

### REPORTS\model-tests\google_gemini_report.md:42
- **Type:** api_key_generic
- **Description:** Generic API key detected
- **Pattern:** `API_KEY=your-google-api-key-here`
- **Fix:** Use environment variable

## 🛡️ Security Recommendations
1. **Never commit API keys or secrets to version control**
2. **Use environment variables for all sensitive data**
3. **Implement proper secret management**
4. **Regular security scans**
5. **Use .gitignore to exclude sensitive files**
