import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const [currentGame, setCurrentGame] = useState('Your Game');
  const [gameInput, setGameInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastPrompt, setLastPrompt] = useState('');
  const [isSwiping, setIsSwiping] = useState(false);

  const isGeneratingRef = useRef(false);
  const gameContainerRef = useRef(null);
  const [isGameActive, setIsGameActive] = useState(false);

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
        setTimeout(() => { try { window.location.reload(); } catch { } }, 200);
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
      setIsSwiping(false);
    }
  };

  // Fetch a concise idea from backend Anthropic endpoint
  const fetchIdeaFromAnthropic = async () => {
    const res = await fetch('http://localhost:8080/generate-idea', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!res.ok) throw new Error('idea_generation_failed');
    const data = await res.json();
    if (!data?.idea) throw new Error('idea_generation_failed');
    return String(data.idea).trim();
  };

  const handleGameSubmit = (e) => {
    e.preventDefault();
    if (gameInput.trim()) {
      updateGameViaFreestyle(gameInput.trim());
      setGameInput('');
    }
  };

  // Prevent page scroll from stealing controls while game is active/focused/hovered
  useEffect(() => {
    if (!isGameActive) return;

    const scrollKeys = new Set(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' ', 'Space', 'PageUp', 'PageDown', 'Home', 'End']);

    const onKeyDown = (e) => {
      if (scrollKeys.has(e.key)) {
        e.preventDefault();
      }
    };
    const onWheel = (e) => {
      e.preventDefault();
    };
    const onTouchMove = (e) => {
      e.preventDefault();
    };

    window.addEventListener('keydown', onKeyDown, { capture: false });
    window.addEventListener('wheel', onWheel, { passive: false });
    window.addEventListener('touchmove', onTouchMove, { passive: false });

    return () => {
      window.removeEventListener('keydown', onKeyDown, { capture: false });
      window.removeEventListener('wheel', onWheel);
      window.removeEventListener('touchmove', onTouchMove);
    };
  }, [isGameActive]);

  // Auto-start with a default game (once per tab)
  useEffect(() => {
    const FLAG = 'autoInitDone';
    if (sessionStorage.getItem(FLAG)) return;
    if (isGeneratingRef.current) return;

    (async () => {
      try {
        sessionStorage.setItem(FLAG, '1');
        const idea = 'flappy bird game';
        setLastPrompt(idea);
        setCurrentGame(`Generating ${idea}...`);
        await updateGameViaFreestyle(idea);
      } catch (e) {
        console.warn('Auto-init failed', e);
      }
    })();
  }, []);

  const handleNextClick = async () => {
    if (isGeneratingRef.current || isSwiping) return;
    setIsSwiping(true);
    setTimeout(async () => {
      try {
        const idea = await fetchIdeaFromAnthropic();
        await updateGameViaFreestyle(idea);
      } catch (e) {
        console.warn('Idea fetch failed', e);
        setIsSwiping(false);
      }
    }, 120);
  };

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

        <div
          ref={gameContainerRef}
          className={`game-stage ${isSwiping ? 'swipe' : ''}`}
          tabIndex={0}
          onFocus={() => setIsGameActive(true)}
          onBlur={() => setIsGameActive(false)}
          onMouseEnter={() => setIsGameActive(true)}
          onMouseLeave={() => setIsGameActive(false)}
          onClick={() => gameContainerRef.current && gameContainerRef.current.focus()}
        >
          <GameZone currentGame={currentGame} />
        </div>

        <button className="next-cta" onClick={handleNextClick} disabled={isGenerating || isSwiping}>
          <span className="next-cta-arrow">▲</span>
          <span>Swipe for next</span>
        </button>
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
