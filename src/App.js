import React, { useEffect, useState } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const [currentGame, setCurrentGame] = useState("Your Game");
  const [gameInput, setGameInput] = useState("");

  const updateGameViaFreestyle = async (gameName) => {
    try {
      const response = await fetch('http://localhost:8080/gamezone/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ game_name: gameName }),
      });

      if (response.ok) {
        console.log(`Game updated to: ${gameName}`);
        setCurrentGame(gameName);
      } else {
        console.error('Failed to update game via Freestyle');
      }
    } catch (error) {
      console.error('Error calling Freestyle API:', error);
    }
  };

  const handleGameSubmit = (e) => {
    e.preventDefault();
    if (gameInput.trim()) {
      updateGameViaFreestyle(gameInput);
      setGameInput("");
    }
  };

  const handleScroll = () => {
    console.log('Scroll detected - calling Freestyle update function');

    const scrollY = window.scrollY;
    const scrollThreshold = 200;

    if (scrollY > scrollThreshold) {
      updateGameViaFreestyle("Advanced Game Mode");
    } else {
      updateGameViaFreestyle("Your Game");
    }
  };

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <div className="App">
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

        <div className="scroll-indicator">
          <p>Scroll to interact with the game!</p>
        </div>
      </div>
    </div>
  );
}

export default App;
