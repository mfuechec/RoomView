import { useAppState } from '../hooks/useAppState'
import './Toolbar.css'

function Toolbar() {
  const { state, dispatch } = useAppState()

  const handleExport = () => {
    const exportData = {
      export_version: '1.0',
      exported_at: new Date().toISOString(),
      blueprint: {
        file_name: state.blueprint.fileName,
        dimensions: state.blueprint.dimensions
      },
      detection_results: {
        original: state.detectedRooms,
        edited: state.editedRooms,
        summary: {
          rooms_detected: state.detectedRooms.length,
          rooms_after_editing: state.editedRooms.filter(r => !r.isDeleted).length,
          user_added: state.editedRooms.filter(r => r.isUserCreated).length,
          user_modified: state.editedRooms.filter(r => r.isModified).length,
          user_deleted: state.editedRooms.filter(r => r.isDeleted).length
        }
      }
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `roomview_${state.sessionId}_${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleReset = () => {
    if (confirm('Are you sure you want to clear all data?')) {
      dispatch({ type: 'RESET' })
    }
  }

  const handleExportGroundTruth = () => {
    // Filter out deleted rooms
    const activeRooms = state.editedRooms.filter(r => !r.isDeleted)

    const groundTruth = {
      sample_id: state.blueprint.fileName.replace(/\.[^/.]+$/, ''), // Remove extension
      blueprint_type: 'single_floor', // User can manually edit if multi-floor
      created_at: new Date().toISOString(),
      total_rooms: activeRooms.length,
      image_dimensions: state.blueprint.dimensions,
      rooms: activeRooms.map(room => ({
        id: room.id,
        bounding_box_normalized: room.bounding_box_normalized,
        polygon_normalized: room.polygon_normalized || null,
        confidence_score: room.confidence_score || 1.0,
        isUserCreated: room.isUserCreated || false,
        isUserVerified: true, // Mark as verified ground truth
        type_hint: room.type_hint || 'room'
      }))
    }

    const blob = new Blob([JSON.stringify(groundTruth, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${groundTruth.sample_id}_ground_truth.json`
    link.click()
    URL.revokeObjectURL(url)

    console.log('Ground truth exported:', groundTruth)
  }

  const hasBlueprint = state.blueprint.dataUrl !== null

  const handleToggleEditMode = () => {
    dispatch({ type: 'TOGGLE_EDIT_MODE' })
  }

  const handleSetDrawingTool = (tool) => {
    dispatch({ type: 'SET_DRAWING_TOOL', payload: tool })
  }

  return (
    <div className="toolbar">
      <h2 className="toolbar-title">Tools</h2>

      {/* EDIT MODE TOGGLE */}
      {hasBlueprint && (
        <div className="toolbar-edit-mode">
          <button
            className={`toolbar-button ${state.editMode ? 'edit-active' : 'edit-inactive'}`}
            onClick={handleToggleEditMode}
            data-testid="edit-mode-toggle"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            {state.editMode ? 'Exit Edit Mode' : 'Edit Mode'}
          </button>

          {/* Drawing Tool Selector - only show in edit mode */}
          {state.editMode && (
            <div className="drawing-tools">
              <button
                className={`tool-btn ${state.drawingTool === 'select' ? 'active' : ''}`}
                onClick={() => handleSetDrawingTool('select')}
                title="Select and modify rooms"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z" />
                </svg>
              </button>
              <button
                className={`tool-btn ${state.drawingTool === 'box' ? 'active' : ''}`}
                onClick={() => handleSetDrawingTool('box')}
                title="Draw box"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <rect x="3" y="3" width="18" height="18" />
                </svg>
              </button>
              <button
                className={`tool-btn ${state.drawingTool === 'polygon' ? 'active' : ''}`}
                onClick={() => handleSetDrawingTool('polygon')}
                title="Draw polygon"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <polygon points="12 2 2 19 12 15 22 19" />
                </svg>
              </button>
            </div>
          )}
        </div>
      )}

      <div className="toolbar-actions">
        <button
          className="toolbar-button primary"
          onClick={handleExport}
          disabled={!hasBlueprint}
          data-testid="export-btn"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export JSON
        </button>

        {state.editMode && (
          <button
            className="toolbar-button ground-truth"
            onClick={handleExportGroundTruth}
            disabled={!hasBlueprint || state.editedRooms.filter(r => !r.isDeleted).length === 0}
            data-testid="export-ground-truth-btn"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="18" x2="12" y2="12" />
              <line x1="9" y1="15" x2="15" y2="15" />
            </svg>
            Export Ground Truth
          </button>
        )}

        <button
          className="toolbar-button secondary"
          onClick={handleReset}
          disabled={!hasBlueprint}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          Reset
        </button>
      </div>

      {hasBlueprint && (
        <div className="toolbar-info">
          <h3 className="toolbar-info-title">Session Info</h3>
          <dl className="toolbar-info-list">
            <dt>Blueprint:</dt>
            <dd>{state.blueprint.fileName}</dd>

            <dt>Rooms Detected:</dt>
            <dd>{state.detectedRooms.length}</dd>

            <dt>Active Rooms:</dt>
            <dd>{state.editedRooms.filter(r => !r.isDeleted).length}</dd>

            <dt>Status:</dt>
            <dd className="status">{state.processingStatus}</dd>
          </dl>
        </div>
      )}
    </div>
  )
}

export default Toolbar
