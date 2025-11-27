# Frontend React Component Snippet (JSX)

This snippet provides a reusable React component pattern used in the repo (Material-UI, Plotly, Waveform-style usage).

Usage: copy into `frontend/src/components/YourComponent.jsx` and import into `App.js` or adjacent component.

```jsx
import React from 'react'
import Paper from '@mui/material/Paper'
import Box from '@mui/material/Box'
import PropTypes from 'prop-types'
// Optional: Plotly or WaveSurfer for audio
// import Plot from 'react-plotly.js'

const YourComponent = ({title, data, onAction}) => {
  return (
    <Paper elevation={2} style={{padding: '16px'}}>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <h3>{title}</h3>
        <button onClick={onAction}>Action</button>
      </Box>

      {/* Example: Waveform or Plotly visualization */}
      {/* <Plot data={data} layout={{height: 240, width: 800}} /> */}

      <div>
        {/* Example: factor cards or content area */}
        <p>Insert component content here</p>
      </div>
    </Paper>
  )
}

YourComponent.propTypes = {
  title: PropTypes.string,
  data: PropTypes.object,
  onAction: PropTypes.func
}

YourComponent.defaultProps = {
  title: 'Your Component',
  data: {},
  onAction: () => {}
}

export default YourComponent
```

Integration notes:

- Add tests for components using `@testing-library/react` if modifying UI behavior.
- Use `npm start` to run frontend server and `npm test` for component tests.
- Use existing `frontend/src/components/` patterns (e.g., `FactorCard.jsx`, `WaveformDashboard.jsx`) for style and hooks.
