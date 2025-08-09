import React, { useEffect, useState } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const [currentGameIndex, setCurrentGameIndex] = useState(0);
  
  const games = [
    "Snake Game - Eat the apples!",
    "Pong - Classic paddle game",
    "Tetris - Stack the blocks",
    "Space Invaders - Defend Earth!",
    "Pac-Man - Eat all the dots",
    "Breakout - Break all the bricks",
    "Frogger - Cross the road safely"
  ];

  const handleScroll = () => {
    console.log('Hello World - Scroll detected!');
    
    // Change game on scroll - simple scroll-based switching
    const scrollY = window.scrollY;
    const scrollThreshold = 100; // Change game every 100px of scroll
    const newGameIndex = Math.floor(scrollY / scrollThreshold) % games.length;
    
    if (newGameIndex !== currentGameIndex) {
      setCurrentGameIndex(newGameIndex);
    }
  };

  const handlePlayGame = () => {
    console.log(`Play specific game button clicked! Current game: ${games[currentGameIndex]}`);
  };

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [currentGameIndex]);

  return (
    <div className="App">
      <div className="content-container">
        <button className="play-button" onClick={handlePlayGame}>
          Play Specific Game
        </button>
        
        <GameZone currentGame={games[currentGameIndex]} />
        
        <div className="scroll-indicator">
          <p>Scroll to discover new games!</p>
          <p>Game {currentGameIndex + 1} of {games.length}</p>
        </div>
      </div>
    </div>
  );
}

export default App;
