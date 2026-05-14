import React, { useState, useEffect, useRef, use } from 'react';
import { io } from 'socket.io-client';

// Connecting to backend
const socket = io('http://localhost:5000');

function App() {
  const [playerRole, setPlayerRole] = useState('Connecting...')
  const [logs, setLogs] = useState([])
  const logsEndRef = useRef(null)
  const [gameStarted, setGameStarted] = useState(false)
  const [lockedCharacter, setLockedCharacter] = useState(null)
  const [winner, setWinner] = useState(null)
  const [currentTurn, setCurrentTurn] = useState(null)
  const [wagerLocked, setWagerLocked] = useState(false)

  useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])
  
  useEffect(() => {
    socket.on('role_assignment', (data) => {
      setPlayerRole(data.role)
    })

    socket.on('turn_start', (data) => {
      setCurrentTurn(data.turn)
      setWagerLocked(false) // Unlock wagers at the start of each turn
    })

    socket.on('wager_reset', () => {
      setCurrentTurn(null)
      setWagerLocked(false) // Unlock wagers when they are reset
    })


    socket.on('game_update', (data) => {
      setLogs((prevLogs) => [...prevLogs, data.message])
    })

    socket.on('match_start', (data) => {
      setGameStarted(true)
      setLogs((prevLogs) => [...prevLogs, data.message, 'The match has started!'])
    })

    socket.on('match_end', (data) => {
      setWinner(data.message.split('!')[0]) // Extract the winner's name
    })

    socket.on('game_reset', () => {
      setGameStarted(false)
      setLockedCharacter(null)
      setWinner(null)
      setLogs([])
    })
    // Clean up the socket connection on unmount
    return () => {
      socket.off('role_assignment')
      socket.off('game_update')
      socket.off('match_start')
      socket.off('match_end')
      socket.off('game_reset')
      socket.off('turn_start')
      socket.off('wager_reset')
    }
  }, [])

  const handleAttack = () => {
    socket.emit('player_action', { attackType: 'Basic Attack' })
  }

  const handleSelectCharacter = (character) => {
    socket.emit('character_selection', { character })
    setLockedCharacter(character)
  };

  const handleResetGame = () => {
    socket.emit('reset_game')
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>Aetherium Clash</h1>
      <p> Role: {playerRole}</p>
      <p> Locked Character: {lockedCharacter}</p>

      {/* CHARACTER SELECTION PHASE */}
      {playerRole !== 'Spectator' && !gameStarted && !lockedCharacter && (
        <div style={{ marginBottom: '20px' }}>
          <h2>Select Your Character:</h2>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            <button onClick={() => handleSelectCharacter('Aha')}>Aha</button>
            <button onClick={() => handleSelectCharacter('Lan')}>Lan</button>
            <button onClick={() => handleSelectCharacter('Yaoshi')}>Yaoshi</button>
          </div>
        </div>
      )}

      {/* WAITING ROOM */}
      {playerRole !== 'Spectator' && !gameStarted && lockedCharacter && (
        <div style={{ marginBottom: '20px' }}>
          <h2>Waiting for Other Players...</h2>
          <p> You have selected <strong style={{ color: 'blue' }}>{lockedCharacter}</strong></p>
        </div>
      )}

      {/* COMBAT PHASE */}
      {playerRole !== 'Spectator' && gameStarted && !winner && (
        <div style={{ marginBottom: '20px' }}>
          
          {/* PHASE 1: RPS */}
          {!currentTurn && (
            <div>
              <h2>Rock, Paper, Scissors Phase</h2>
              {wagerLocked ? (
                <p>Waiting for opponent to make a move...</p>
              ) : (
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button onClick={() => { socket.emit('submit_wager', { wager: 'Rock' }); setWagerLocked(true); }}>Rock</button>
                  <button onClick={() => { socket.emit('submit_wager', { wager: 'Paper' }); setWagerLocked(true); }}>Paper</button>
                  <button onClick={() => { socket.emit('submit_wager', { wager: 'Scissors' }); setWagerLocked(true); }}>Scissors</button>
              </div>
            )}
          </div>
        )}

        {/* PHASE 2: WON RPS, GAIN TURN */}
        {currentTurn === playerRole && (
          <div>
            <h2>You won the RPS! You gain a turn.</h2>
            <button onClick={handleAttack}>Basic Attack</button>
          </div>
        )}

        {/* PHASE 3: LOST RPS */}
        {currentTurn && currentTurn !== playerRole && (
          <div>
            <h2>You lost the RPS. Opponent's turn.</h2>
          </div>
        )}
      </div>
    )}

      {/* GAMEOVER PHASE */}
      {winner && (
        <div style={{ marginBottom: '20px' }}>
          <h2>Game Over</h2>
          <p>The winner is: <strong style={{ color: 'green' }}>{winner}</strong></p>
          <button onClick={handleResetGame}>Reset Game</button>
        </div>
      )}

      <h2 style={{ marginTop: '20px' }}>Battle Logs:</h2>
      <ul style={{ background: '#f0f0f0', padding: '10px', borderRadius: '5px', listStyleType: 'none', color: 'black', 'height': '250px', 'overflowY': 'auto' }}>
        {logs.map((log, index) => <li key={index} style={{ marginBottom: '5px' }}>{log}</li>)}
        <div ref={logsEndRef} />
      </ul>
    </div>
  );
}

export default App;