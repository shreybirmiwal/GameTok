import React from 'react';

const GameZone = ({ currentGame }) => {
  // Simple HTML content zone - perfect for Morph apply!
  // Just put your HTML game content here and it will render
  // this is the html content that will be rendered in the game zone ONLY CHANGE THIS ZONE
  const htmlContent = `
    <div style="text-align: center; padding: 20px;">
      <h2>🎮 HTML Game Zone</h2>
      <p>This is where your HTML5 Canvas games will appear!</p>
      <div style="background: linear-gradient(45deg, #ff6b6b, #4ecdc4); padding: 20px; border-radius: 10px; color: white; margin: 20px 0;">
        <strong>Perfect for Morph Apply!</strong><br/>
        Just replace the htmlContent variable above with your generated HTML5 game code
      </div>
      <div style="border: 2px dashed #ccc; padding: 40px; margin: 20px 0; border-radius: 8px;">
        <p style="color: #666; font-style: italic;">
          🎯 Game content will render here<br/>
          📝 Use Morph to apply HTML5 Canvas games directly<br/>
          🚀 No complex React components needed!
        </p>
      </div>
      <p style="font-size: 12px; color: #888;">
        Current game: ${currentGame || 'None selected'}
      </p>
    </div>
  `;

  return (
    <div className="game-zone">
      <div className="game-content">
        <div dangerouslySetInnerHTML={{ __html: htmlContent }} />
      </div>
    </div>
  );
};

export default GameZone;