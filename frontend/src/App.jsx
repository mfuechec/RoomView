import { useState } from 'react'
import { AppStateProvider } from './hooks/useAppState'
import Header from './components/Header'
import BlueprintUploader from './components/BlueprintUploader'
import BlueprintCanvas from './components/BlueprintCanvas'
import RoomList from './components/RoomList'
import Toolbar from './components/Toolbar'
import ErrorDisplay from './components/ErrorDisplay'
import './App.css'

function App() {
  return (
    <AppStateProvider>
      <div className="app">
        <Header />

        <main className="app-main">
          <div className="app-left">
            <BlueprintUploader />
            <RoomList />
          </div>

          <div className="app-center">
            <BlueprintCanvas />
          </div>

          <div className="app-right">
            <Toolbar />
          </div>
        </main>

        <ErrorDisplay />
      </div>
    </AppStateProvider>
  )
}

export default App
