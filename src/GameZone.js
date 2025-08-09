import React, { useEffect, useRef, useState } from 'react';

// React GameZone scaffold. Morph will replace this entire file with a generated React game component.
const GameZone = ({ currentGame }) => {
  const canvasRef = useRef(null);
  const [message] = useState('Ready');

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#0f0';
    ctx.font = '16px monospace';
    ctx.fillText('Setting up...', 90, 150);
  }, [currentGame]);

  return (
    <div style={{ textAlign: 'center', padding: 16 }}>
      <h3 style={{ marginBottom: 12 }}>{currentGame || 'Your Game'}</h3>
      <canvas ref={canvasRef} width={400} height={300} style={{ border: '2px solid #333', background: '#fff' }} />
      <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>{message}</div>
    </div>
  );
};

export default GameZone;