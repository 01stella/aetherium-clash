import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';

// Connecting to backend
const socket = io('http://localhost:5000');

function App() {
  const [playerRole, setPlayerRole] = useState('Connecting...')
  const [logs, setLogs] = useState([])

  useEffect(() => {
    socket.on('role_assignment', (data) => {
      setPlayerRole(data.role)
    })

    socket.on('game_update', (data) => {
      setLogs((prevLogs) => [...prevLogs, data.message])
    })

    // Clean up the socket connection on unmount
    return () => {
      socket.off('role_assignment')
      socket.off('game_update')
    }
  }, [])

  const handleAttack = () => {
    socket.emit('player_action', { attackType: 'Basic Attack' })
  }

  const handleSelectCharacter = (character) => {
    socket.emit('character_selection', { character })
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Aetherium Clash</h1>
      <p> Role: {playerRole}</p>
    
      {playerRole !== 'Spectator' && (
        <div style={{ marginBottom: '20px' }}>
          <h2>Select Your Character:</h2>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            <button onClick={() => handleSelectCharacter('Aha')}>Aha</button>
            <button onClick={() => handleSelectCharacter('Lan')}>Lan</button>
            <button onClick={() => handleSelectCharacter('Yaoshi')}>Yaoshi</button>
          </div>
          
          <button onClick={handleAttack}>Attack</button>
        </div>
      )}

      <h2 style={{ marginTop: '20px' }}>Battle Logs:</h2>
      <ul style={{ background: '#f0f0f0', padding: '10px', borderRadius: '5px', listStyleType: 'none', color: 'black' }}>
        {logs.map((log, index) => <li key={index} style={{ marginBottom: '5px' }}>{log}</li>)}
      </ul>
    </div>
  );
}

export default App;