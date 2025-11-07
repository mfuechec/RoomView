import { useAppState } from '../hooks/useAppState'
import './ErrorDisplay.css'

function ErrorDisplay() {
  const { state, dispatch } = useAppState()

  if (!state.error) return null

  const errorConfig = {
    INVALID_FORMAT: {
      title: 'Unsupported File Format',
      icon: '⚠️'
    },
    FILE_TOO_LARGE: {
      title: 'File Too Large',
      icon: '📏'
    },
    NO_ROOMS_FOUND: {
      title: 'No Rooms Detected',
      icon: '🔍'
    },
    TIMEOUT: {
      title: 'Processing Timeout',
      icon: '⏱️'
    },
    NETWORK_ERROR: {
      title: 'Connection Failed',
      icon: '📡'
    },
    INTERNAL_ERROR: {
      title: 'Server Error',
      icon: '❌'
    }
  }

  const config = errorConfig[state.error.code] || errorConfig.NETWORK_ERROR

  const handleClose = () => {
    dispatch({ type: 'CLEAR_ERROR' })
  }

  return (
    <div className="error-overlay" onClick={handleClose}>
      <div className="error-dialog" onClick={(e) => e.stopPropagation()} data-testid="error-message">
        <button className="error-close" onClick={handleClose}>×</button>

        <div className="error-icon">{config.icon}</div>
        <h3 className="error-title">{config.title}</h3>
        <p className="error-message">{state.error.message}</p>

        {state.error.suggestions && state.error.suggestions.length > 0 && (
          <div className="error-suggestions">
            <strong>Suggestions:</strong>
            <ul>
              {state.error.suggestions.map((suggestion, i) => (
                <li key={i}>{suggestion}</li>
              ))}
            </ul>
          </div>
        )}

        <button className="error-button" onClick={handleClose}>
          Close
        </button>
      </div>
    </div>
  )
}

export default ErrorDisplay
