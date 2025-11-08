import { useRef } from 'react'
import { useAppState } from '../hooks/useAppState'
import { uploadBlueprint, mockUploadBlueprint } from '../services/api'
import { validateBlueprint } from '../utils/validation'
import './BlueprintUploader.css'

// Use mock API for development (toggle based on backend availability)
const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === 'true'

function BlueprintUploader() {
  const { state, dispatch } = useAppState()
  const fileInputRef = useRef(null)

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file
    const errors = validateBlueprint(file)
    if (errors.length > 0) {
      dispatch({
        type: 'SET_ERROR',
        payload: {
          code: errors[0].code,
          message: errors[0].message
        }
      })
      return
    }

    // Read file as data URL for preview
    const reader = new FileReader()
    reader.onload = async (event) => {
      dispatch({
        type: 'SET_BLUEPRINT',
        payload: {
          file,
          dataUrl: event.target.result,
          fileName: file.name,
          dimensions: { width: 0, height: 0 } // Will be set after image loads
        }
      })

      // Start upload
      dispatch({ type: 'SET_STATUS', payload: 'uploading' })

      try {
        const result = USE_MOCK_API
          ? await mockUploadBlueprint(file)
          : await uploadBlueprint(file)

        dispatch({
          type: 'SET_DETECTED_ROOMS',
          payload: result  // Pass entire result with rooms and doorways
        })
        dispatch({ type: 'SET_STATUS', payload: 'complete' })
      } catch (error) {
        dispatch({
          type: 'SET_ERROR',
          payload: {
            code: error.code || 'NETWORK_ERROR',
            message: error.message || 'Failed to upload blueprint',
            suggestions: error.suggestions
          }
        })
        dispatch({ type: 'SET_STATUS', payload: 'error' })
      }
    }

    reader.readAsDataURL(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) {
      fileInputRef.current.files = e.dataTransfer.files
      handleFileSelect({ target: { files: [file] } })
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const isProcessing = state.processingStatus === 'uploading' ||
                       state.processingStatus === 'processing'

  return (
    <div className="uploader">
      <h2 className="uploader-title">Upload Blueprint</h2>

      <div
        className={`uploader-dropzone ${isProcessing ? 'uploading' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => !isProcessing && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,application/pdf"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          data-testid="file-input"
        />

        {isProcessing ? (
          <div className="uploader-loading" data-testid="processing-indicator">
            <div className="spinner"></div>
            <p>Processing blueprint...</p>
            <small>This may take up to 30 seconds</small>
          </div>
        ) : (
          <div className="uploader-prompt">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p className="uploader-text">
              Drag & drop blueprint here<br />
              <span>or click to browse</span>
            </p>
            <small className="uploader-hint">
              PNG, JPG, or PDF • Max 10MB
            </small>
          </div>
        )}
      </div>

      {state.blueprint.fileName && (
        <div className="uploader-file-info">
          <strong>Selected:</strong> {state.blueprint.fileName}
        </div>
      )}
    </div>
  )
}

export default BlueprintUploader
