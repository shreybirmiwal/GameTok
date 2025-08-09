import React, { useEffect } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const handleScroll = () => {
    console.log('Hello World - Scroll detected!');
  };

  const handlePlayGame = () => {
    console.log('Play specific game button clicked!');
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
        <button className="play-button" onClick={handlePlayGame}>
          Play Specific Game
        </button>
        
        <GameZone />
        
        <div className="scroll-content">
          <p>Scroll up to load next game!</p>
          <p>More content here...</p>
          <p>Keep scrolling...</p>
        </div>
      </div>
    </div>
  );
}

export default App;
