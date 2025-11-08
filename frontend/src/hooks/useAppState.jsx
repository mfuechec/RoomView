import { createContext, useContext, useReducer, useEffect } from 'react'
import { v4 as uuidv4 } from 'uuid'

const AppStateContext = createContext(null)

const initialState = {
  blueprint: {
    file: null,
    dataUrl: null,
    fileName: '',
    dimensions: { width: 0, height: 0 },
    uploadedAt: null
  },
  detectedRooms: [],
  editedRooms: [],
  processingStatus: 'idle', // 'idle' | 'uploading' | 'processing' | 'complete' | 'error'
  selectedRoomId: null,
  editMode: false, // NEW: Edit mode toggle
  drawingTool: 'box', // NEW: 'box' | 'polygon' | 'select'
  error: null,
  sessionId: uuidv4(),
  lastSaved: null
}

function appReducer(state, action) {
  switch (action.type) {
    case 'SET_BLUEPRINT':
      return {
        ...state,
        blueprint: { ...action.payload, uploadedAt: new Date().toISOString() },
        processingStatus: 'processing'
      }

    case 'SET_STATUS':
      return {
        ...state,
        processingStatus: action.payload
      }

    case 'SET_DETECTED_ROOMS':
      return {
        ...state,
        detectedRooms: action.payload,
        editedRooms: action.payload,
        processingStatus: 'complete'
      }

    case 'SELECT_ROOM':
      return {
        ...state,
        selectedRoomId: action.payload
      }

    case 'DELETE_ROOM':
      return {
        ...state,
        editedRooms: state.editedRooms.map(room =>
          room.id === action.payload
            ? { ...room, isDeleted: true }
            : room
        )
      }

    case 'ADD_ROOM':
      return {
        ...state,
        editedRooms: [
          ...state.editedRooms,
          { ...action.payload, isUserCreated: true }
        ]
      }

    case 'UPDATE_ROOM':
      return {
        ...state,
        editedRooms: state.editedRooms.map(room =>
          room.id === action.payload.id
            ? { ...room, ...action.payload, isModified: true }
            : room
        )
      }

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        processingStatus: 'error'
      }

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      }

    case 'TOGGLE_EDIT_MODE':
      return {
        ...state,
        editMode: !state.editMode,
        selectedRoomId: null // Deselect when toggling
      }

    case 'SET_DRAWING_TOOL':
      return {
        ...state,
        drawingTool: action.payload
      }

    case 'RESET':
      return {
        ...initialState,
        sessionId: uuidv4()
      }

    case 'RESTORE_STATE':
      return {
        ...state,
        ...action.payload
      }

    default:
      return state
  }
}

export function AppStateProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState)

  // Persist state to LocalStorage
  useEffect(() => {
    if (state.blueprint.dataUrl) {
      try {
        const serialized = JSON.stringify({
          blueprint: {
            fileName: state.blueprint.fileName,
            dataUrl: state.blueprint.dataUrl,
            dimensions: state.blueprint.dimensions
          },
          detectedRooms: state.detectedRooms,
          editedRooms: state.editedRooms,
          sessionId: state.sessionId,
          lastSaved: new Date().toISOString()
        })

        localStorage.setItem('roomview_session', serialized)
      } catch (e) {
        console.error('Failed to save state to LocalStorage:', e)
      }
    }
  }, [state.blueprint, state.detectedRooms, state.editedRooms, state.sessionId])

  // Restore state on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('roomview_session')
      if (saved) {
        const parsed = JSON.parse(saved)
        dispatch({ type: 'RESTORE_STATE', payload: parsed })
      }
    } catch (e) {
      console.error('Failed to restore state from LocalStorage:', e)
    }
  }, [])

  return (
    <AppStateContext.Provider value={{ state, dispatch }}>
      {children}
    </AppStateContext.Provider>
  )
}

export function useAppState() {
  const context = useContext(AppStateContext)
  if (!context) {
    throw new Error('useAppState must be used within AppStateProvider')
  }
  return context
}
