import './Header.css'

function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">
          <span className="header-icon">🏗️</span>
          RoomView
        </h1>
        <p className="header-subtitle">AI-Powered Blueprint Room Detection</p>
      </div>
    </header>
  )
}

export default Header
