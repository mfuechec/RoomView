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

  const hasBlueprint = state.blueprint.dataUrl !== null

  return (
    <div className="toolbar">
      <h2 className="toolbar-title">Tools</h2>

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
