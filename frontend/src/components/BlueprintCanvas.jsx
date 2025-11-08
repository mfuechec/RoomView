import { useEffect, useRef, useState, useCallback } from 'react'
import { useAppState } from '../hooks/useAppState'
import './BlueprintCanvas.css'

function BlueprintCanvas() {
  const { state, dispatch } = useAppState()
  const canvasRef = useRef(null)
  const [canvasState, setCanvasState] = useState({
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    imgWidth: 0,
    imgHeight: 0
  })
  const [isDrawing, setIsDrawing] = useState(false)
  const [drawStart, setDrawStart] = useState(null)
  const [currentDrawRect, setCurrentDrawRect] = useState(null)
  const [resizeState, setResizeState] = useState(null) // { roomId, handle: 'nw'|'ne'|'sw'|'se', originalBounds }
  const [polygonPoints, setPolygonPoints] = useState([]) // Array of {x, y} canvas coordinates for polygon being drawn
  const [currentMousePos, setCurrentMousePos] = useState(null) // For drawing line from last point to mouse

  // Redraw canvas when rooms or selection changes
  useEffect(() => {
    if (!state.blueprint.dataUrl || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const img = new Image()

    img.onload = () => {
      // Set canvas size to match container
      const container = canvas.parentElement
      canvas.width = container.clientWidth
      canvas.height = container.clientHeight

      // Calculate scale and position
      const scale = Math.min(
        canvas.width / img.width,
        canvas.height / img.height
      )

      const x = (canvas.width - img.width * scale) / 2
      const y = (canvas.height - img.height * scale) / 2

      // Save canvas state for hit testing
      setCanvasState({
        scale,
        offsetX: x,
        offsetY: y,
        imgWidth: img.width,
        imgHeight: img.height
      })

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, x, y, img.width * scale, img.height * scale)

      // Draw rooms
      if (state.editedRooms.length > 0) {
        drawRooms(ctx, state.editedRooms, img.width, img.height, x, y, scale)
      }

      // Draw doorways
      if (state.doorways && state.doorways.length > 0) {
        drawDoorways(ctx, state.doorways, img.width, img.height, x, y, scale)
      }

      // Draw current drawing rectangle
      if (currentDrawRect) {
        ctx.strokeStyle = '#f56565'
        ctx.lineWidth = 2
        ctx.setLineDash([5, 5])
        ctx.strokeRect(
          currentDrawRect.x,
          currentDrawRect.y,
          currentDrawRect.width,
          currentDrawRect.height
        )
        ctx.setLineDash([])
      }

      // Draw polygon being created
      if (polygonPoints.length > 0) {
        ctx.strokeStyle = '#f56565'
        ctx.fillStyle = 'rgba(245, 101, 101, 0.2)'
        ctx.lineWidth = 2

        // Draw lines between points
        ctx.beginPath()
        ctx.moveTo(polygonPoints[0].x, polygonPoints[0].y)
        for (let i = 1; i < polygonPoints.length; i++) {
          ctx.lineTo(polygonPoints[i].x, polygonPoints[i].y)
        }

        // Draw line to current mouse position
        if (currentMousePos) {
          ctx.setLineDash([5, 5])
          ctx.lineTo(currentMousePos.x, currentMousePos.y)
          ctx.setLineDash([])
        }

        ctx.stroke()

        // Draw points as circles
        polygonPoints.forEach((point, index) => {
          ctx.beginPath()
          ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI)
          ctx.fillStyle = index === 0 ? '#48bb78' : '#f56565' // First point is green
          ctx.fill()
        })
      }
    }

    img.src = state.blueprint.dataUrl
  }, [state.blueprint.dataUrl, state.editedRooms, state.doorways, state.selectedRoomId, currentDrawRect, polygonPoints, currentMousePos])

  // Color palette for room overlays (distinct, vibrant colors)
  const getColorForRoom = (index) => {
    const palette = [
      { stroke: '#667eea', fill: 'rgba(102, 126, 234, 0.15)' },  // Blue
      { stroke: '#f56565', fill: 'rgba(245, 101, 101, 0.15)' },  // Red
      { stroke: '#48bb78', fill: 'rgba(72, 187, 120, 0.15)' },   // Green
      { stroke: '#ed8936', fill: 'rgba(237, 137, 54, 0.15)' },   // Orange
      { stroke: '#9f7aea', fill: 'rgba(159, 122, 234, 0.15)' },  // Purple
      { stroke: '#38b2ac', fill: 'rgba(56, 178, 172, 0.15)' },   // Teal
      { stroke: '#ecc94b', fill: 'rgba(236, 201, 75, 0.15)' },   // Yellow
      { stroke: '#ed64a6', fill: 'rgba(237, 100, 166, 0.15)' },  // Pink
      { stroke: '#4299e1', fill: 'rgba(66, 153, 225, 0.15)' },   // Light Blue
      { stroke: '#f6ad55', fill: 'rgba(246, 173, 85, 0.15)' },   // Peach
    ]
    return palette[index % palette.length]
  }

  const drawRooms = (ctx, rooms, imgWidth, imgHeight, offsetX, offsetY, scale) => {
    rooms.forEach((room, index) => {
      if (room.isDeleted) return

      const [xMin, yMin, xMax, yMax] = room.bounding_box_normalized

      const x = offsetX + xMin * imgWidth * scale
      const y = offsetY + yMin * imgHeight * scale
      const width = (xMax - xMin) * imgWidth * scale
      const height = (yMax - yMin) * imgHeight * scale

      const isSelected = room.id === state.selectedRoomId

      // Get unique color for this room based on index
      const colors = getColorForRoom(index)
      let strokeColor = colors.stroke
      let fillColor = colors.fill

      // Override with green highlight if selected
      if (isSelected) {
        fillColor = 'rgba(72, 187, 120, 0.3)' // Brighter green for selected
      }

      // Check if room has polygon data
      if (room.polygon_normalized && room.polygon_normalized.length >= 3) {
        // Draw polygon shape
        const polygonPoints = room.polygon_normalized.map(([normX, normY]) => ({
          x: offsetX + normX * imgWidth * scale,
          y: offsetY + normY * imgHeight * scale
        }))

        // Fill polygon
        ctx.fillStyle = fillColor
        ctx.beginPath()
        ctx.moveTo(polygonPoints[0].x, polygonPoints[0].y)
        for (let i = 1; i < polygonPoints.length; i++) {
          ctx.lineTo(polygonPoints[i].x, polygonPoints[i].y)
        }
        ctx.closePath()
        ctx.fill()

        // Stroke polygon
        ctx.strokeStyle = strokeColor
        ctx.lineWidth = isSelected ? 4 : 2
        ctx.stroke()

        // Draw bounding box as dashed outline (to show overall bounds)
        ctx.setLineDash([5, 5])
        ctx.strokeStyle = strokeColor
        ctx.lineWidth = 1
        ctx.strokeRect(x, y, width, height)
        ctx.setLineDash([])
      } else {
        // Draw regular bounding box (no polygon data)
        ctx.strokeStyle = strokeColor
        ctx.lineWidth = isSelected ? 4 : 2
        ctx.strokeRect(x, y, width, height)

        ctx.fillStyle = fillColor
        ctx.fillRect(x, y, width, height)
      }

      // Draw room ID
      ctx.fillStyle = '#2d3748'
      ctx.font = isSelected ? 'bold 14px sans-serif' : '12px sans-serif'
      ctx.fillText(room.id, x + 4, y + 16)

      // Draw resize handles for selected room (in edit mode)
      if (isSelected && state.editMode) {
        const handleSize = 8
        ctx.fillStyle = '#48bb78'
        // Corner handles
        ctx.fillRect(x - handleSize / 2, y - handleSize / 2, handleSize, handleSize)
        ctx.fillRect(x + width - handleSize / 2, y - handleSize / 2, handleSize, handleSize)
        ctx.fillRect(x - handleSize / 2, y + height - handleSize / 2, handleSize, handleSize)
        ctx.fillRect(x + width - handleSize / 2, y + height - handleSize / 2, handleSize, handleSize)
      }
    })
  }

  const drawDoorways = (ctx, doorways, imgWidth, imgHeight, offsetX, offsetY, scale) => {
    doorways.forEach((doorway) => {
      if (!doorway.center_normalized) return

      const [centerX, centerY] = doorway.center_normalized
      const cx = offsetX + centerX * imgWidth * scale
      const cy = offsetY + centerY * imgHeight * scale

      // Draw based on doorway type
      if (doorway.type === 'arc' && doorway.radius_normalized) {
        // Arc doorway: draw as red arc circle showing door swing
        const radius = doorway.radius_normalized * imgWidth * scale

        ctx.strokeStyle = '#f56565'
        ctx.lineWidth = 2
        ctx.setLineDash([4, 4])
        ctx.beginPath()
        ctx.arc(cx, cy, radius, 0, 2 * Math.PI)
        ctx.stroke()
        ctx.setLineDash([])

        // Draw center point
        ctx.fillStyle = '#f56565'
        ctx.beginPath()
        ctx.arc(cx, cy, 4, 0, 2 * Math.PI)
        ctx.fill()
      } else {
        // Gap doorway: draw as solid red circle marker
        ctx.fillStyle = '#f56565'
        ctx.strokeStyle = '#c53030'
        ctx.lineWidth = 1.5
        ctx.beginPath()
        ctx.arc(cx, cy, 6, 0, 2 * Math.PI)
        ctx.fill()
        ctx.stroke()
      }
    })
  }

  // Hit test to find room at coordinates
  const getRoomAtPosition = (canvasX, canvasY) => {
    const { scale, offsetX, offsetY, imgWidth, imgHeight } = canvasState

    for (let i = state.editedRooms.length - 1; i >= 0; i--) {
      const room = state.editedRooms[i]
      if (room.isDeleted) continue

      const [xMin, yMin, xMax, yMax] = room.bounding_box_normalized
      const x = offsetX + xMin * imgWidth * scale
      const y = offsetY + yMin * imgHeight * scale
      const width = (xMax - xMin) * imgWidth * scale
      const height = (yMax - yMin) * imgHeight * scale

      if (canvasX >= x && canvasX <= x + width &&
          canvasY >= y && canvasY <= y + height) {
        return room
      }
    }
    return null
  }

  // Check if mouse is over a resize handle
  const getResizeHandle = (canvasX, canvasY) => {
    if (!state.selectedRoomId || !state.editMode) return null

    const selectedRoom = state.editedRooms.find(r => r.id === state.selectedRoomId && !r.isDeleted)
    if (!selectedRoom) return null

    const { scale, offsetX, offsetY, imgWidth, imgHeight } = canvasState
    const [xMin, yMin, xMax, yMax] = selectedRoom.bounding_box_normalized

    const x1 = offsetX + xMin * imgWidth * scale
    const y1 = offsetY + yMin * imgHeight * scale
    const x2 = offsetX + xMax * imgWidth * scale
    const y2 = offsetY + yMax * imgHeight * scale

    const handleSize = 12 // Slightly larger hit area than visual size
    const tolerance = handleSize / 2

    // Check each corner
    if (Math.abs(canvasX - x1) <= tolerance && Math.abs(canvasY - y1) <= tolerance) {
      return { roomId: selectedRoom.id, handle: 'nw' } // Top-left
    }
    if (Math.abs(canvasX - x2) <= tolerance && Math.abs(canvasY - y1) <= tolerance) {
      return { roomId: selectedRoom.id, handle: 'ne' } // Top-right
    }
    if (Math.abs(canvasX - x1) <= tolerance && Math.abs(canvasY - y2) <= tolerance) {
      return { roomId: selectedRoom.id, handle: 'sw' } // Bottom-left
    }
    if (Math.abs(canvasX - x2) <= tolerance && Math.abs(canvasY - y2) <= tolerance) {
      return { roomId: selectedRoom.id, handle: 'se' } // Bottom-right
    }

    return null
  }

  // Handle canvas click
  const handleCanvasClick = (e) => {
    if (!state.editMode) return

    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    // Polygon mode: add points
    if (state.drawingTool === 'polygon') {
      // Check if clicking near first point to close polygon
      if (polygonPoints.length >= 3) {
        const firstPoint = polygonPoints[0]
        const distance = Math.sqrt(Math.pow(x - firstPoint.x, 2) + Math.pow(y - firstPoint.y, 2))

        if (distance < 15) {
          // Close polygon and create room
          completePolygon()
          return
        }
      }

      // Add new point
      setPolygonPoints([...polygonPoints, { x, y }])
      return
    }

    // Select mode
    if (state.drawingTool === 'select') {
      const room = getRoomAtPosition(x, y)
      if (room) {
        dispatch({ type: 'SELECT_ROOM', payload: room.id })
      } else {
        dispatch({ type: 'SELECT_ROOM', payload: null })
      }
    }
  }

  // Complete polygon and create room
  const completePolygon = () => {
    if (polygonPoints.length < 3) {
      setPolygonPoints([])
      return
    }

    const { scale, offsetX, offsetY, imgWidth, imgHeight } = canvasState

    // Convert canvas coordinates to normalized coordinates
    const polygonNormalized = polygonPoints.map(point => [
      Math.max(0, Math.min(1, (point.x - offsetX) / (imgWidth * scale))),
      Math.max(0, Math.min(1, (point.y - offsetY) / (imgHeight * scale)))
    ])

    // Calculate bounding box from polygon
    const xCoords = polygonNormalized.map(p => p[0])
    const yCoords = polygonNormalized.map(p => p[1])
    const xMin = Math.min(...xCoords)
    const yMin = Math.min(...yCoords)
    const xMax = Math.max(...xCoords)
    const yMax = Math.max(...yCoords)

    const newRoom = {
      id: `room_${Date.now()}`,
      bounding_box_normalized: [xMin, yMin, xMax, yMax],
      polygon_normalized: polygonNormalized,
      isUserCreated: true,
      confidence_score: 1.0
    }

    dispatch({ type: 'ADD_ROOM', payload: newRoom })
    setPolygonPoints([])
    setCurrentMousePos(null)
  }

  // Handle mouse down for drawing
  const handleMouseDown = (e) => {
    if (!state.editMode) return

    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    // Priority 1: Check if clicking on a resize handle
    const handle = getResizeHandle(x, y)
    if (handle && state.drawingTool === 'select') {
      const room = state.editedRooms.find(r => r.id === handle.roomId)
      setResizeState({
        roomId: handle.roomId,
        handle: handle.handle,
        originalBounds: [...room.bounding_box_normalized]
      })
      return
    }

    // Priority 2: Drawing new box
    if (state.drawingTool === 'box') {
      setIsDrawing(true)
      setDrawStart({ x, y })
    }
  }

  // Handle mouse move for drawing or resizing
  const handleMouseMove = (e) => {
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top

    // Track mouse position for polygon preview line
    if (state.drawingTool === 'polygon' && polygonPoints.length > 0) {
      setCurrentMousePos({ x: mouseX, y: mouseY })
    }

    // Handle resizing
    if (resizeState) {
      const { scale, offsetX, offsetY, imgWidth, imgHeight } = canvasState
      const room = state.editedRooms.find(r => r.id === resizeState.roomId)
      if (!room) return

      // Convert mouse position to normalized coordinates
      const normX = Math.max(0, Math.min(1, (mouseX - offsetX) / (imgWidth * scale)))
      const normY = Math.max(0, Math.min(1, (mouseY - offsetY) / (imgHeight * scale)))

      let [xMin, yMin, xMax, yMax] = resizeState.originalBounds

      // Update bounds based on which handle is being dragged
      switch (resizeState.handle) {
        case 'nw': // Top-left
          xMin = Math.min(normX, xMax - 0.02) // Prevent flipping
          yMin = Math.min(normY, yMax - 0.02)
          break
        case 'ne': // Top-right
          xMax = Math.max(normX, xMin + 0.02)
          yMin = Math.min(normY, yMax - 0.02)
          break
        case 'sw': // Bottom-left
          xMin = Math.min(normX, xMax - 0.02)
          yMax = Math.max(normY, yMin + 0.02)
          break
        case 'se': // Bottom-right
          xMax = Math.max(normX, xMin + 0.02)
          yMax = Math.max(normY, yMin + 0.02)
          break
      }

      // Update the room
      dispatch({
        type: 'UPDATE_ROOM',
        payload: {
          id: resizeState.roomId,
          bounding_box_normalized: [xMin, yMin, xMax, yMax]
        }
      })
      return
    }

    // Handle drawing new box
    if (isDrawing) {
      setCurrentDrawRect({
        x: Math.min(drawStart.x, mouseX),
        y: Math.min(drawStart.y, mouseX),
        width: Math.abs(mouseX - drawStart.x),
        height: Math.abs(mouseY - drawStart.y)
      })
    }
  }

  // Handle mouse up to complete drawing or resizing
  const handleMouseUp = (e) => {
    // Handle resize complete
    if (resizeState) {
      setResizeState(null)
      return
    }

    // Handle drawing complete
    if (isDrawing) {
      const canvas = canvasRef.current
      const rect = canvas.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      // Convert canvas coordinates to normalized coordinates
      const { scale, offsetX, offsetY, imgWidth, imgHeight } = canvasState

      const x1 = Math.min(drawStart.x, x)
      const y1 = Math.min(drawStart.y, y)
      const x2 = Math.max(drawStart.x, x)
      const y2 = Math.max(drawStart.y, y)

      // Convert to normalized coordinates
      const xMinNorm = Math.max(0, Math.min(1, (x1 - offsetX) / (imgWidth * scale)))
      const yMinNorm = Math.max(0, Math.min(1, (y1 - offsetY) / (imgHeight * scale)))
      const xMaxNorm = Math.max(0, Math.min(1, (x2 - offsetX) / (imgWidth * scale)))
      const yMaxNorm = Math.max(0, Math.min(1, (y2 - offsetY) / (imgHeight * scale)))

      // Only add if rectangle has reasonable size
      const minSize = 0.01 // 1% of image
      if ((xMaxNorm - xMinNorm) > minSize && (yMaxNorm - yMinNorm) > minSize) {
        const newRoom = {
          id: `room_${Date.now()}`,
          bounding_box_normalized: [xMinNorm, yMinNorm, xMaxNorm, yMaxNorm],
          isUserCreated: true,
          confidence_score: 1.0
        }

        dispatch({ type: 'ADD_ROOM', payload: newRoom })
      }

      setIsDrawing(false)
      setDrawStart(null)
      setCurrentDrawRect(null)
    }
  }

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!state.editMode) return

      if (e.key === 'Delete' && state.selectedRoomId) {
        dispatch({ type: 'DELETE_ROOM', payload: state.selectedRoomId })
      } else if (e.key === 'Escape') {
        // Cancel polygon drawing or deselect room
        if (polygonPoints.length > 0) {
          setPolygonPoints([])
          setCurrentMousePos(null)
        } else {
          dispatch({ type: 'SELECT_ROOM', payload: null })
        }
      } else if (e.key === 'Enter' && polygonPoints.length >= 3) {
        // Complete polygon on Enter key
        completePolygon()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [state.editMode, state.selectedRoomId, polygonPoints, dispatch])

  if (!state.blueprint.dataUrl) {
    return (
      <div className="canvas-empty">
        <p>Upload a blueprint to get started</p>
      </div>
    )
  }

  return (
    <div className="canvas-container">
      <canvas
        ref={canvasRef}
        className={`canvas ${state.editMode ? 'edit-mode' : ''} ${state.drawingTool === 'box' ? 'cursor-crosshair' : ''}`}
        onClick={handleCanvasClick}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          if (isDrawing) {
            setIsDrawing(false)
            setDrawStart(null)
            setCurrentDrawRect(null)
          }
          if (resizeState) {
            setResizeState(null)
          }
        }}
      />
      {state.editMode && (
        <div className="edit-mode-hint">
          {state.drawingTool === 'select' && !state.selectedRoomId && 'Click to select room'}
          {state.drawingTool === 'select' && state.selectedRoomId && 'Drag corners to resize • Delete key to remove'}
          {state.drawingTool === 'box' && 'Click and drag to draw room'}
          {state.drawingTool === 'polygon' && polygonPoints.length === 0 && 'Click to add points • Draw L-shaped rooms'}
          {state.drawingTool === 'polygon' && polygonPoints.length > 0 && polygonPoints.length < 3 && `${polygonPoints.length} points added • Need at least 3 points`}
          {state.drawingTool === 'polygon' && polygonPoints.length >= 3 && 'Click near first point to close • Enter to complete • Escape to cancel'}
        </div>
      )}
    </div>
  )
}

export default BlueprintCanvas
