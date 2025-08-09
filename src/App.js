import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const [currentGame, setCurrentGame] = useState('Your Game');
  const [gameInput, setGameInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastPrompt, setLastPrompt] = useState('');

  const sentinelRef = useRef(null);
  const isGeneratingRef = useRef(false);
  const canScrollTriggerRef = useRef(true);

  const updateGameViaFreestyle = async (gameName) => {
    try {
      setIsGenerating(true);
      isGeneratingRef.current = true;
      setLastPrompt(gameName);
      setCurrentGame(`Generating ${gameName}...`);

      const response = await fetch('http://localhost:8080/generate-game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_idea: gameName }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Game generated successfully:', result);
        setCurrentGame(gameName);
      } else {
        const error = await response.json();
        console.error('Failed to generate game:', error);
        setCurrentGame(`Failed to generate ${gameName}`);
      }
    } catch (error) {
      console.error('Error calling game generation API:', error);
      setCurrentGame(`Error generating ${gameName}`);
    } finally {
      setIsGenerating(false);
      isGeneratingRef.current = false;
    }
  };

  // Local fallback idea generator
  const generateIdeaLocally = () => {
    const adjectives = ['Tiny', 'Cosmic', 'Retro', 'Neon', 'Shadow', 'Pixel', 'Turbo', 'Mystic', 'Swift', 'Lucky'];
    const nouns = ['Runner', 'Climber', 'Racer', 'Dodger', 'Miner', 'Glider', 'Jumper', 'Fisher', 'Courier', 'Knight'];
    const mechanics = [
      'tap to jump over obstacles and collect coins',
      'hold to charge a jump and time landings on moving platforms',
      'swipe to change lanes and avoid traffic',
      'drag to slingshot between anchors while avoiding spikes',
      'tap to hook and swing past gaps',
      'tap to dive and resurface to collect treasures',
      'hold-and-release to dash through breakable walls',
      'tap to flip gravity and stay on the track',
      'tap to fish and upgrade your rod between runs',
      'tap to deliver packages while dodging drones',
    ];
    const worlds = ['in a neon city', 'in a haunted forest', 'on floating islands', 'in retro space', 'inside a cave', 'on rooftops'];
    const a = adjectives[Math.floor(Math.random() * adjectives.length)];
    const n = nouns[Math.floor(Math.random() * nouns.length)];
    const m = mechanics[Math.floor(Math.random() * mechanics.length)];
    const w = worlds[Math.floor(Math.random() * worlds.length)];
    return `${a} ${n}: ${m} ${w}.`;
  };

  // Fetch a concise idea from backend Anthropic endpoint
  const fetchIdeaFromAnthropic = async () => {
    try {
      const res = await fetch('http://localhost:8080/generate-idea', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error('Bad response');
      const data = await res.json();
      if (data && typeof data.idea === 'string' && data.idea.trim().length > 0) {
        return data.idea.trim();
      }
      throw new Error('No idea in response');
    } catch (e) {
      console.warn('Anthropic idea endpoint failed, using local fallback', e);
      return generateIdeaLocally();
    }
  };

  const handleGameSubmit = (e) => {
    e.preventDefault();
    if (gameInput.trim()) {
      updateGameViaFreestyle(gameInput.trim());
      setGameInput('');
    }
  };

  // Bottom scroll: when sentinel enters viewport, generate one new idea
  useEffect(() => {
    const handler = async () => {
      if (isGeneratingRef.current) return;
      if (!canScrollTriggerRef.current) return;
      canScrollTriggerRef.current = false;
      const idea = await fetchIdeaFromAnthropic();
      await updateGameViaFreestyle(idea);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting) {
          handler();
        } else {
          // Reset once the sentinel leaves the viewport so user must scroll back to bottom again
          canScrollTriggerRef.current = true;
        }
      },
      { root: null, rootMargin: '100px', threshold: 0 }
    );

    if (sentinelRef.current) observer.observe(sentinelRef.current);
    return () => observer.disconnect();
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

        {/* Spacer to enable scrolling to bottom on simple screens */}
        <div className="scroll-spacer" />
        {/* Sentinel for infinite scroll */}
        <div ref={sentinelRef} className="scroll-sentinel" />
      </div>

      {lastPrompt && (
        <div className="prompt-footer" title={lastPrompt}>
          {lastPrompt}
        </div>
      )}

      {isGenerating && <div className="generate-status">Generating...</div>}
    </div>
  );
}

export default App;
