import { useAppState } from '../hooks/useAppState'
import './RoomList.css'

function RoomList() {
  const { state, dispatch } = useAppState()

  const activeRooms = state.editedRooms.filter(r => !r.isDeleted)

  const handleRoomClick = (roomId) => {
    dispatch({ type: 'SELECT_ROOM', payload: roomId })
  }

  const handleDeleteRoom = (roomId) => {
    dispatch({ type: 'DELETE_ROOM', payload: roomId })
  }

  if (activeRooms.length === 0) {
    return (
      <div className="room-list">
        <h2 className="room-list-title">Detected Rooms</h2>
        <p className="room-list-empty">No rooms detected yet</p>
      </div>
    )
  }

  return (
    <div className="room-list">
      <h2 className="room-list-title">
        Detected Rooms ({activeRooms.length})
      </h2>

      <div className="room-list-items">
        {activeRooms.map((room) => (
          <div
            key={room.id}
            className={`room-item ${state.selectedRoomId === room.id ? 'selected' : ''}`}
            onClick={() => handleRoomClick(room.id)}
            data-testid="room-box"
          >
            <div className="room-item-header">
              <span className="room-item-id">{room.id}</span>
              <button
                className="room-item-delete"
                onClick={(e) => {
                  e.stopPropagation()
                  handleDeleteRoom(room.id)
                }}
                data-testid="delete-room-btn"
                title="Delete room"
              >
                ×
              </button>
            </div>

            <div className="room-item-details">
              <span className="room-item-type">{room.type_hint || 'room'}</span>
              {room.confidence_score && (
                <span className="room-item-confidence">
                  {Math.round(room.confidence_score * 100)}%
                </span>
              )}
            </div>

            {room.isUserCreated && (
              <span className="room-item-badge">Manual</span>
            )}
            {room.isModified && (
              <span className="room-item-badge modified">Edited</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default RoomList
