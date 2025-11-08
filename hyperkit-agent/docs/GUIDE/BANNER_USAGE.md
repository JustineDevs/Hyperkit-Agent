# HyperAgent ASCII Banner Guide

## Overview

HyperAgent displays a professional ASCII banner on every CLI invocation to establish brand identity and provide a polished user experience.

## Banner Styles

Three banner styles are available:

### 1. Simple (Default)
Clean, readable ASCII art banner:
```
 __    __                                           ______                                  __     
|  \  |  \                                         /      \                                |  \    
| $$  | $$ __    __   ______    ______    ______  |  $$$$$$\  ______    ______   _______  _| $$_   
| $$__| $$|  \  |  \ /      \  /      \  /      \ | $$__| $$ /      \  /      \ |       \|   $$ \  
| $$    $$| $$  | $$|  $$$$$$\|  $$$$$$\|  $$$$$$\| $$    $$|  $$$$$$\|  $$$$$$\| $$$$$$$\\$$$$$$
| $$$$$$$$| $$  | $$| $$  | $$| $$    $$| $$   \$$| $$$$$$$$| $$  | $$| $$    $$| $$  | $$ | $$ __
| $$  | $$| $$__/ $$| $$__/ $$| $$$$$$$$| $$      | $$  | $$| $$__| $$| $$$$$$$$| $$  | $$ | $$|  \
| $$  | $$ \$$    $$| $$    $$ \$$     \| $$      | $$  | $$ \$$    $$ \$$     \| $$  | $$  \$$  $$
 \$$   \$$ _\$$$$$$$| $$$$$$$   \$$$$$$$ \$$       \$$   \$$ _\$$$$$$$  \$$$$$$$ \$$   \$$   \$$$$
          |  \__| $$| $$                                    |  \__| $$
           \$$    $$| $$                                     \$$    $$
            \$$$$$$  \$$                                      \$$$$$$

                                  Autonomous Smart Contract Agent
```

### 2. Compact
Shorter version for terminals with limited height:
```
 __    __                                           ______                                  __     
|  \  |  \                                         /      \                                |  \    
| $$  | $$ __    __   ______    ______    ______  |  $$$$$$\  ______    ______   _______  _| $$_   
| $$__| $$|  \  |  \ /      \  /      \  /      \ | $$__| $$ /      \  /      \ |       \|   $$ \  
| $$    $$| $$  | $$|  $$$$$$\|  $$$$$$\|  $$$$$$\| $$    $$|  $$$$$$\|  $$$$$$\| $$$$$$$\\$$$$$$
| $$$$$$$$| $$  | $$| $$  | $$| $$    $$| $$   \$$| $$$$$$$$| $$  | $$| $$    $$| $$  | $$ | $$ __
| $$  | $$| $$__/ $$| $$__/ $$| $$$$$$$$| $$      | $$  | $$| $$__| $$| $$$$$$$$| $$  | $$ | $$|  \
| $$  | $$ \$$    $$| $$    $$ \$$     \| $$      | $$  | $$ \$$    $$ \$$     \| $$  | $$  \$$  $$
 \$$   \$$ _\$$$$$$$| $$$$$$$   \$$$$$$$ \$$       \$$   \$$ _\$$$$$$$  \$$$$$$$ \$$   \$$   \$$$$
          |  \__| $$| $$                                    |  \__| $$
           \$$    $$| $$                                     \$$    $$
            \$$$$$$  \$$                                      \$$$$$$

                                  Autonomous Smart Contract Agent
```

### 3. Professional
Big Money font style (wider, more decorative):
```
 __    __                                           ______                                  __     
|  \  |  \                                         /      \                                |  \    
| $$  | $$ __    __   ______    ______    ______  |  $$$$$$\  ______    ______   _______  _| $$_   
| $$__| $$|  \  |  \ /      \  /      \  /      \ | $$__| $$ /      \  /      \ |       \|   $$ \  
| $$    $$| $$  | $$|  $$$$$$\|  $$$$$$\|  $$$$$$\| $$    $$|  $$$$$$\|  $$$$$$\| $$$$$$$\\$$$$$$
| $$$$$$$$| $$  | $$| $$  | $$| $$    $$| $$   \$$| $$$$$$$$| $$  | $$| $$    $$| $$  | $$ | $$ __
| $$  | $$| $$__/ $$| $$__/ $$| $$$$$$$$| $$      | $$  | $$| $$__| $$| $$$$$$$$| $$  | $$ | $$|  \
| $$  | $$ \$$    $$| $$    $$ \$$     \| $$      | $$  | $$ \$$    $$ \$$     \| $$  | $$  \$$  $$
 \$$   \$$ _\$$$$$$$| $$$$$$$   \$$$$$$$ \$$       \$$   \$$ _\$$$$$$$  \$$$$$$$ \$$   \$$   \$$$$
          |  \__| $$| $$                                    |  \__| $$
           \$$    $$| $$                                     \$$    $$
            \$$$$$$  \$$                                      \$$$$$$

                                  Autonomous Smart Contract Agent
```

## Usage

### Default Behavior
The banner is displayed automatically on every CLI command:
```bash
hyperagent --help
hyperagent version
hyperagent status
```

### Suppress Banner
Use `--no-banner` flag to suppress the banner:
```bash
hyperagent --no-banner version
hyperagent --no-banner --help
```

### Enable Color
Use `--color` flag to enable colored output (requires terminal support):
```bash
hyperagent --color version
```

### Environment Variables

**Banner Style:**
```bash
export HYPERAGENT_BANNER_STYLE=professional  # Options: simple, compact, professional
hyperagent version
```

**Color Support:**
```bash
export HYPERAGENT_COLOR=1  # Enable color output
hyperagent version
```

## Configuration

### Setting Default Style
Add to your `.env` file or shell profile:
```bash
HYPERAGENT_BANNER_STYLE=professional
HYPERAGENT_COLOR=0  # Disable color by default
```

### CI/CD Usage
For CI/CD pipelines, use `--no-banner` to keep logs clean:
```bash
hyperagent --no-banner version
```

## Technical Details

### Compatibility
- **Pure ASCII**: No Unicode characters, works in all terminals
- **Windows Compatible**: Tested on Windows CMD, PowerShell, Git Bash
- **CI/CD Safe**: Works in GitHub Actions, Jenkins, etc.
- **Encoding**: Automatically handles UTF-8 encoding with fallback

### Implementation
- **Location**: `hyperkit-agent/cli/utils/banner.py`
- **Integration**: Called automatically in `cli/main.py`
- **Dependencies**: Uses `rich` library for optional color support

### Banner Display Logic
1. Check `--no-banner` flag → Skip if set
2. Check `HYPERAGENT_BANNER_STYLE` env var → Select style
3. Check `--color` flag or `HYPERAGENT_COLOR` env var → Apply color if enabled
4. Print banner with tagline
5. Continue with command execution

## Best Practices

### For Development
- Use default banner (simple style)
- Keep color disabled unless testing
- Use `--no-banner` in scripts/automation

### For Production
- Use professional style for demos
- Enable color for user-facing terminals
- Suppress banner in CI/CD logs

### For Documentation
- Show banner in README screenshots
- Document banner customization options
- Include banner in demo videos

## Troubleshooting

### Banner Not Displaying
- Check if `--no-banner` flag is set
- Verify `HYPERAGENT_BANNER_STYLE` is valid
- Check terminal encoding (should be UTF-8)

### Encoding Errors
- Banner automatically falls back to ASCII-only
- No action needed - fallback is automatic

### Color Not Working
- Verify terminal supports ANSI colors
- Check `--color` flag or `HYPERAGENT_COLOR` env var
- Color is optional - banner works without it

---

**Last Updated**: 2025-11-07  
**Status**: ✅ Production Ready

