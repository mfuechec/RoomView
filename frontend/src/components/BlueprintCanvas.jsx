import { useEffect, useRef } from 'react'
import { useAppState } from '../hooks/useAppState'
import './BlueprintCanvas.css'

function BlueprintCanvas() {
  const { state } = useAppState()
  const canvasRef = useRef(null)

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

      // Draw blueprint
      const scale = Math.min(
        canvas.width / img.width,
        canvas.height / img.height
      )

      const x = (canvas.width - img.width * scale) / 2
      const y = (canvas.height - img.height * scale) / 2

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, x, y, img.width * scale, img.height * scale)

      // Draw rooms
      if (state.editedRooms.length > 0) {
        drawRooms(ctx, state.editedRooms, img.width, img.height, x, y, scale)
      }
    }

    img.src = state.blueprint.dataUrl
  }, [state.blueprint.dataUrl, state.editedRooms])

  const drawRooms = (ctx, rooms, imgWidth, imgHeight, offsetX, offsetY, scale) => {
    rooms.forEach((room, index) => {
      if (room.isDeleted) return

      const [xMin, yMin, xMax, yMax] = room.bounding_box_normalized

      const x = offsetX + xMin * imgWidth * scale
      const y = offsetY + yMin * imgHeight * scale
      const width = (xMax - xMin) * imgWidth * scale
      const height = (yMax - yMin) * imgHeight * scale

      // Draw bounding box
      ctx.strokeStyle = room.isUserCreated ? '#f56565' : '#667eea'
      ctx.lineWidth = 2
      ctx.strokeRect(x, y, width, height)

      // Draw semi-transparent fill
      ctx.fillStyle = room.isUserCreated ? 'rgba(245, 101, 101, 0.1)' : 'rgba(102, 126, 234, 0.1)'
      ctx.fillRect(x, y, width, height)

      // Draw room ID
      ctx.fillStyle = '#2d3748'
      ctx.font = '12px sans-serif'
      ctx.fillText(room.id, x + 4, y + 16)
    })
  }

  if (!state.blueprint.dataUrl) {
    return (
      <div className="canvas-empty">
        <p>Upload a blueprint to get started</p>
      </div>
    )
  }

  return (
    <div className="canvas-container">
      <canvas ref={canvasRef} className="canvas" />
    </div>
  )
}

export default BlueprintCanvas
