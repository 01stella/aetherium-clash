import React, { useState, useEffect, useLayoutEffect } from 'react';

const Arrows = {
    up: '↑',
    down: '↓',
    left: '←',
    right: '→'
}

const valid_keys = Object.keys(Arrows)

function ComboAttack({ onComplete }) {
    const [combo, setCombo] = useState([])
    const [currentIndex, setCurrentIndex] = useState(0)
    const [timeLeft, setTimeLeft] = useState(3000) // 3 second timer for each input
    const [status, setStatus] = useState('active') // 'active', 'success', 'failed
    
    // GEnerate random combo of 5 inputs
    useEffect(() => {
        const newCombo = Array.from({ length: 5 }, () => valid_keys[Math.floor(Math.random() * valid_keys.length)])
        setCombo(newCombo)
    }, [])

    // 2 second countdown
    useEffect(() => {
        if (status !== 'active') return

        const timer = setInterval(() => {
            setTimeLeft((prev) => {
                const nextTime = Math.round((prev - 0.1) * 10) / 10 // round to 1 decimal place

                if (nextTime <= 0) {
                    clearInterval(timer)
                    setStatus('failed')
                    setTimeout(() => onComplete(1.0), 1000) // failed: no multiplier (1.0x)
                    return 0
                }
                return nextTime
            })
        }, 100)

        return () => clearInterval(timer)
    }, [status, onComplete])

    // Handle key presses
    useEffect(() => {
        if (status != 'active') return

        const handleKeyDown = (e) => {

            if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.code)) {
                e.preventDefault()
            } // prevent arrow keys from scrolling page
            // A, W, S, D to arrow keys so they can use either
            let key = e.key
            if (key === 'ArrowUp' || key.toLowerCase() === 'w') key = 'up'
            if (key === 'ArrowLeft' || key.toLowerCase() === 'a') key = 'left'
            if (key === 'ArrowDown' || key.toLowerCase() === 's') key = 'down'
            if (key === 'ArrowRight' || key.toLowerCase() === 'd') key = 'right'

            if (!valid_keys.includes(key)) return

            if (key === combo[currentIndex]) {
                // correct input
                const nextIndex = currentIndex + 1
                setCurrentIndex(nextIndex)

                if (nextIndex === 5) {
                    setStatus('success')
                    setTimeout(() => onComplete(1.15), 1000) // success: 1.15x multiplier
                }
            } else {
                // wrong input, fail immediately
                setStatus('failed')
                setTimeout(() => onComplete(1.0), 1000) // failed: no multiplier (1.0x)
            }
        }

        window.addEventListener('keydown', handleKeyDown, { passive: false })
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [currentIndex, combo, status, onComplete])

    return (
        <div style={{ textAlign: 'center', backgroundColor: '#222', padding: '20px', borderRadius: '10px', border: '2px solid #555' }}>
            <h3 style={{ margin: '0 0 10px 0', color: 'white' }}>Combo Attack!</h3>

            {/* timer display */}
            <div style={{ fontsize: '24px', fontWeight: 'bold', color: status === 'failed' ? 'red' : status === 'success' ? '#4caf50' : 'white', marginBottom: '10px' }}>
                {status === 'success' ? 'Perfect!' : status === 'failed' ? 'Failed!' : `Time Left: ${timeLeft}s`}
            </div>

            {/* arrow display */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '15px' }}>
                {combo.map((key, index) => (
                    <div key={index} style={{ opacity: index < currentIndex ? 1 : 0.5,  // highlight current input
                    transform: index === currentIndex ? 'scale(1.2)' : 'scale(1)', // enlarge current input
                    transition: 'all 0.1s ease-in-out'}}>
                        {Arrows[key]}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ComboAttack;