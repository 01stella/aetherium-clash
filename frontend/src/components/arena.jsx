import React from 'react';

function Arena({ socket, playerRole, matchCharacters, currentTurn, wagerLocked, setWagerLocked }) {
    const me = playerRole === 'Player2' ? 'Player2' : 'Player1'
    const opponent = playerRole === 'Player2' ? 'Player1' : 'Player2'

    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '20px' }}>

            {/* 'ME' SIDE (Left)' */}
            <div style={{ width: '40%', textAlign: 'center' }}>
                <div style={{ width: '100px', height: '100px', background: '#333', borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center', margin: '0 auto' }}>
                {/* Placeholder for character image */}
                <p style={{ paddingTop: '130px', color: '#888'}}>{me}</p>
                </div>
            </div>

            {/* ARENA MIDDLE */}
            <div style={{ width: '20%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>

                {/* RPS PHASE */}
                {!currentTurn && !wagerLocked && (
                    <>
                        <h3 style={{ margin: '0' }}>RPS Phase</h3>
                        <button style={{ width: '150px', padding: '15px', cursor: 'pointer' }} onClick={() => { socket.emit('submit_wager', { wager: 'Rock' }); setWagerLocked(true); }}>Rock</button>
                        <button style={{ width: '150px', padding: '15px', cursor: 'pointer' }} onClick={() => { socket.emit('submit_wager', { wager: 'Paper' }); setWagerLocked(true); }}>Paper</button>
                        <button style={{ width: '150px', padding: '15px', cursor: 'pointer' }} onClick={() => { socket.emit('submit_wager', { wager: 'Scissors' }); setWagerLocked(true); }}>Scissors</button>
                    </>
                )}

                {/* WAITING FOR OPPONENT TO RPS */}
                {!currentTurn && wagerLocked && (
                    <p style={{ color: '#aaa' }}>Waiting for opponent...</p>
                )}
                
                {/* QTE MINIGAME HERE LATER!! */}
            
            </div>
            
            {/* OPPONENT SIDE (Right)' */}
            <div style={{ width: '40%', textAlign: 'center' }}>
                <div style={{ width: '100px', height: '100px', background: '#333', borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center', margin: '0 auto' }}>
                {/* Placeholder for character image */}
                <p style={{ paddingTop: '130px', color: '#888'}}>{opponent}</p>
                </div>
            </div>

        </div>
    );
}

export default Arena;