---
applyTo: "frontend/**/*.{js,jsx,ts,tsx}"
---

# Frontend Development Guidelines

## React Code Standards

### Component Structure
- Use functional components with hooks (no class components)
- Keep components focused and single-purpose
- Extract reusable logic into custom hooks
- Use composition over inheritance

### Component Organization
```jsx
// Imports
import React, { useState, useEffect } from 'react';
import { Box, Card } from '@mui/material';
import axios from 'axios';

// Component definition
function ComponentName({ prop1, prop2 }) {
  // State declarations
  const [data, setData] = useState(null);
  
  // Effects
  useEffect(() => {
    // Effect logic
  }, [dependencies]);
  
  // Event handlers
  const handleEvent = () => {
    // Handler logic
  };
  
  // Render
  return (
    <Box>
      {/* JSX */}
    </Box>
  );
}

export default ComponentName;
```

### Naming Conventions
- Components: PascalCase (e.g., `WaveformDashboard`, `FactorCard`)
- Functions: camelCase (e.g., `handleSubmit`, `fetchData`)
- Constants: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`, `MAX_RETRIES`)
- CSS classes: kebab-case or camelCase (consistent with project)

## Material-UI (MUI) Usage

### Component Patterns
- Use MUI components consistently throughout the app
- Use the `sx` prop for inline styling
- Create custom theme for consistent styling
- Follow Material Design principles

### Example Styling
```jsx
<Card
  sx={{
    padding: 2,
    marginBottom: 2,
    backgroundColor: 'background.paper',
    '&:hover': {
      boxShadow: 3
    }
  }}
>
  {/* Content */}
</Card>
```

### Responsive Design
- Use MUI's breakpoint system
- Test on mobile, tablet, and desktop viewports
- Use Grid/Stack components for layouts
- Ensure accessibility on all screen sizes

## State Management

### Local State
- Use `useState` for component-local state
- Use `useReducer` for complex state logic
- Keep state as close to where it's used as possible

### Shared State
- Lift state up to nearest common ancestor
- Use context for deeply nested props
- Consider state management library for complex apps

### Data Fetching
```jsx
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

useEffect(() => {
  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/endpoint');
      setData(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  fetchData();
}, [dependencies]);
```

## API Integration

### Axios Configuration
- Create axios instance with base URL
- Handle errors consistently
- Show loading states during requests
- Display user-friendly error messages

### API Endpoints
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const authenticateUser = async (authData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/authenticate`, authData);
    return response.data;
  } catch (error) {
    console.error('Authentication failed:', error);
    throw error;
  }
};
```

### Error Handling
- Display error messages to users
- Log errors for debugging
- Provide retry mechanisms where appropriate
- Handle network failures gracefully

## Visualization Components

### Plotly.js Usage
- Use react-plotly.js wrapper
- Configure responsive layouts
- Use appropriate chart types for data
- Provide interactive features (zoom, pan, hover)
- Example:
```jsx
<Plot
  data={[
    {
      x: xData,
      y: yData,
      type: 'scatter',
      mode: 'lines',
      name: 'Signal'
    }
  ]}
  layout={{
    title: 'Waveform',
    autosize: true,
    responsive: true,
    xaxis: { title: 'Time (ms)' },
    yaxis: { title: 'Amplitude' }
  }}
  config={{ responsive: true }}
  style={{ width: '100%', height: '400px' }}
/>
```

### WaveSurfer.js Integration
- Initialize with proper container ref
- Handle audio loading and playback
- Add region markers for annotations
- Clean up instances on unmount

## Component-Specific Patterns

### WaveformDashboard
- Display audio waveform with Plotly
- Show authentication results
- Include factor cards with expandable details
- Support demo data loading

### FactorCard
- Display factor name and score
- Use color coding for pass/fail status
- Show expandable evidence details
- Include visual indicators (icons, badges)

### RiskScoreBox
- Visual risk score display with color coding
- List contributing risk factors
- Show risk level (low/medium/high)
- Update dynamically based on assessment

### EvidenceModal
- Tabbed interface for different evidence types
- Display detailed factor results
- Show raw data and analysis
- Support JSON formatting for technical data

## Routing

### React Router Setup
- Define routes in main App component
- Use nested routes where appropriate
- Handle 404 pages
- Example:
```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/history" element={<History />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
```

## Testing

### Component Testing
- Use React Testing Library
- Test user interactions, not implementation
- Use `@testing-library/react` for rendering
- Use `@testing-library/user-event` for interactions

### Test Structure
```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import FactorCard from './FactorCard';

describe('FactorCard', () => {
  it('displays factor name and score', () => {
    render(<FactorCard name="Voice" score={0.95} />);
    expect(screen.getByText('Voice')).toBeInTheDocument();
    expect(screen.getByText('0.95')).toBeInTheDocument();
  });
  
  it('expands on click', () => {
    render(<FactorCard name="Voice" score={0.95} />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText('Evidence')).toBeInTheDocument();
  });
});
```

## Performance Optimization

### Rendering
- Use `React.memo()` for expensive components
- Use `useMemo()` for expensive calculations
- Use `useCallback()` for callback props
- Avoid unnecessary re-renders

### Code Splitting
- Use dynamic imports for large components
- Split routes with React.lazy()
- Use Suspense for loading states

### Bundle Size
- Analyze bundle with `npm run build`
- Remove unused dependencies
- Use tree-shaking where possible
- Lazy load heavy libraries (Plotly, WaveSurfer)

## Accessibility

### Semantic HTML
- Use appropriate HTML elements
- Add ARIA labels where needed
- Ensure keyboard navigation works
- Test with screen readers

### Example
```jsx
<button
  aria-label="Expand factor details"
  onClick={handleExpand}
>
  <ExpandIcon />
</button>
```

## Styling

### CSS-in-JS with MUI
- Use `sx` prop for component-specific styles
- Use theme for consistent design tokens
- Create styled components for reusable elements
- Follow mobile-first approach

### Theme Configuration
```javascript
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
});
```

## Build Configuration

### Dependencies
- Install with `npm install --legacy-peer-deps` due to peer dependency conflicts
- Keep dependencies up to date (security patches)
- Document any special installation requirements

### Environment Variables
- Use `.env` for environment-specific config
- Prefix with `REACT_APP_` for Create React App
- Never commit `.env` files with secrets
- Document required variables in README

### Build Output
- Production builds go to `build/` directory
- Ensure build artifacts are in `.gitignore`
- Optimize assets (images, fonts) before building
- Test production build locally before deployment

## Development Workflow

### Hot Reloading
- Use `npm start` for development server
- Changes auto-reload in browser
- Errors displayed in browser console and terminal

### Debugging
- Use React DevTools browser extension
- Use browser console for logging
- Add breakpoints in browser DevTools
- Use `console.log` sparingly in production code

## Code Quality

### Linting
- Use ESLint for code linting
- Fix linting errors before committing
- Follow existing lint configuration
- Run `npm run lint` to check

### Code Review Checklist
- Components are properly typed/documented
- No console errors in browser
- Responsive on all screen sizes
- Accessibility requirements met
- Performance optimized
- Tests pass (if applicable)
