import React, { useState } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const [currentGame, setCurrentGame] = useState("Your Game");
  const [gameInput, setGameInput] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectStatus, setConnectStatus] = useState("");

  const updateGameViaFreestyle = async (gameName) => {
    try {
      console.log(`Generating game: ${gameName}`);
      setCurrentGame(`Generating ${gameName}...`);

      const response = await fetch('http://localhost:8080/generate-game', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ game_idea: gameName }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log(`Game generated successfully:`, result);
        setCurrentGame(gameName);
      } else {
        const error = await response.json();
        console.error('Failed to generate game:', error);
        setCurrentGame(`Failed to generate ${gameName}`);
      }
    } catch (error) {
      console.error('Error calling game generation API:', error);
      setCurrentGame(`Error generating ${gameName}`);
    }
  };

  const handleGameSubmit = (e) => {
    e.preventDefault();
    if (gameInput.trim()) {
      updateGameViaFreestyle(gameInput);
      setGameInput("");
    }
  };

  const handleReconnect = async () => {
    try {
      setIsConnecting(true);
      setConnectStatus("Connecting...");
      const res = await fetch('http://localhost:8080/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (data.success) {
        setConnectStatus('Connected');
      } else {
        setConnectStatus(`Failed: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Reconnect error', err);
      setConnectStatus('Error connecting');
    } finally {
      setIsConnecting(false);
      // Clear status after a short delay
      setTimeout(() => setConnectStatus(""), 4000);
    }
  };

  return (
    <div className="App">
      {/* Reconnect button - fixed top-right */}
      <button
        onClick={handleReconnect}
        disabled={isConnecting}
        style={{
          position: 'fixed',
          top: 12,
          right: 12,
          zIndex: 1000,
          padding: '8px 12px',
          background: '#222',
          color: '#fff',
          border: '1px solid #444',
          borderRadius: 8,
          cursor: isConnecting ? 'not-allowed' : 'pointer'
        }}
        aria-label="Reconnect to dev server"
      >
        {isConnecting ? 'Reconnecting...' : 'Reconnect'}
      </button>
      {connectStatus && (
        <div style={{ position: 'fixed', top: 52, right: 12, zIndex: 1000, fontSize: 12, color: '#ccc' }}>
          {connectStatus}
        </div>
      )}

      <div className="content-container">
        <div className="game-input-section">
          <h2>What game do you want to play?</h2>
          <form onSubmit={handleGameSubmit}>
            <input
              type="text"
              value={gameInput}
              onChange={(e) => setGameInput(e.target.value)}
              placeholder="Enter game idea..."
              className="game-input"
            />
            <button type="submit" className="submit-button">
              Generate Game
            </button>
          </form>
        </div>

        <GameZone currentGame={currentGame} />
      </div>
    </div>
  );
}

export default App;
