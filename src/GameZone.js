import React from 'react';

const GameZone = ({ currentGame }) => {
  return (
    <div className="game-zone">
      <div className="game-content">
        <h2>{currentGame}</h2>
        <p>🎮 Game will load here</p>
      </div>
    </div>
  );
};

export default GameZone;