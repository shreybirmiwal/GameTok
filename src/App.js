import React, { useEffect, useState } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const [currentGame, setCurrentGame] = useState("Your Game");
  const [gameInput, setGameInput] = useState("");

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
