import React from 'react';

function CombatHUD({ playerRole, currentHP, playerSP, matchCharacters }) {
    {/* if current user is player2, they are 'me'. otherwise, player 1 is me */}
    const me = playerRole === 'Player2' ? 'Player2' : 'Player1' 
    const opponent = playerRole === 'Player2' ? 'Player1' : 'Player2'

    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '20px', color: 'white' }}>

            {/* 'ME' SIDE (Left)' */}
            <div style={{ textAlign: 'left' }}>
                <h3 style={{ margin: '0', color: 'lightblue'}}>{me} (You)</h3>
                <p style={{ margin: '5px 0', fontSize: '14px', color: 'lightgray', fontStyle: 'italic' }}>{matchCharacters[me]}</p>
                <p style={{ margin: '5px 0', fontSize: '16px', fontWeight: 'bold' }}>HP: <span style={{ color: 'lightgreen' }}>{currentHP[me]}</span></p>
                <p style={{ margin: '5px 0', fontSize: '16px', fontWeight: 'bold' }}>SP: <span style={{ color: 'lightblue' }}>{playerSP[me]} / 5</span></p>
            </div>

            {/* OPPONENT SIDE (Right)' */}
            <div style={{ textAlign: 'right' }}>
                <h3 style={{ margin: '0', color: 'lightgray' }}>{opponent}</h3>
                <p style={{ margin: '5px 0', fontSize: '14px', color: 'lightgray', fontStyle: 'italic' }}>{matchCharacters[opponent]}</p>
                <p style={{ margin: '5px 0', fontSize: '16px', fontWeight: 'bold' }}>HP: <span style={{ color: 'lightgreen' }}>{currentHP[opponent]}</span></p>
                <p style={{ margin: '5px 0', fontSize: '16px', fontWeight: 'bold' }}>SP: <span style={{ color: 'lightblue' }}>{playerSP[opponent]} / 5</span></p>
            </div>

        </div>
    );
}

export default CombatHUD;