# Sonotheia Frontend

This is the React frontend for the Sonotheia Enhanced platform.

## ⚠️ Important Dependency Constraints

**DO NOT UPGRADE DEPENDENCIES BLINDLY.**

The build system interacts with `react-scripts` v5 (Create React App), which has known incompatibilities with the latest bleeding-edge libraries. **Future coding agents must respect these version caps:**

| Package | Max Version | Reason |
|---------|-------------|--------|
| `react` | 18.x | React 19 is not fully supported by `react-scripts` v5 without ejecting. |
| `react-dom` | 18.x | Must match React version. |
| `react-router-dom` | 6.x | v7 requires newer Node/bundler features not present in this setup. |
| `@mui/material` | 5.x | v6+ has breaking style engine changes incompatible with current setup. |
| `@mui/icons-material` | 5.x | Must match MUI core. |

## Running Locally

```bash
# Install dependencies (respecting lockfile)
npm ci

# Start development server
npm start
```
