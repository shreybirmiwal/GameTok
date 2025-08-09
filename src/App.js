import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const [currentGame, setCurrentGame] = useState('Your Game');
  const [gameInput, setGameInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastPrompt, setLastPrompt] = useState('');
  const [nextIdea, setNextIdea] = useState('');
  const [nextToken, setNextToken] = useState('');
  const [queue, setQueue] = useState([]); // [{idea, token}]
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
        setTimeout(() => {
          try { window.location.reload(); } catch { }
        }, 200);
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

  // Prepare a game server-side to reduce latency
  const prepareGame = async (idea) => {
    try {
      const res = await fetch('http://localhost:8080/prepare-game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_idea: idea }),
      });
      const data = await res.json();
      if (res.ok && data?.token) {
        return data.token;
      }
      throw new Error(data?.error || 'prepare failed');
    } catch (e) {
      console.warn('prepare-game failed', e);
      return '';
    }
  };

  const applyPrepared = async (token, idea) => {
    setIsGenerating(true);
    isGeneratingRef.current = true;
    setLastPrompt(idea);
    setCurrentGame(`Generating ${idea}...`);
    try {
      const res = await fetch('http://localhost:8080/apply-prepared', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });
      const data = await res.json();
      if (res.ok && data?.success) {
        setCurrentGame(idea);
        setTimeout(() => { try { window.location.reload(); } catch { } }, 150);
      } else {
        await updateGameViaFreestyle(idea);
      }
    } catch (e) {
      console.warn('apply-prepared failed, falling back', e);
      await updateGameViaFreestyle(idea);
    } finally {
      setIsGenerating(false);
      isGeneratingRef.current = false;
      setIsSwiping(false);
    }
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

  // Preload N ideas + prepare code on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const items = [];
      for (let i = 0; i < 3; i++) {
        const idea = await fetchIdeaFromAnthropic();
        if (cancelled) return;
        const token = await prepareGame(idea);
        if (cancelled) return;
        items.push({ idea, token });
      }
      if (!cancelled) {
        setQueue(items);
        setNextIdea(items[0]?.idea || '');
        setNextToken(items[0]?.token || '');
      }
    })();
    return () => { cancelled = true; };
  }, []);

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
        const token = await prepareGame(idea);
        if (token) {
          await applyPrepared(token, idea);
        } else {
          await updateGameViaFreestyle(idea);
        }
      } catch (e) {
        console.warn('Auto-init failed', e);
      }
    })();
  }, []);

  // After applying one, rotate queue and top up
  const rotateAndTopUpQueue = async () => {
    setQueue((prev) => {
      const [, ...rest] = prev;
      return rest;
    });
    setTimeout(async () => {
      const snapshot = queue.slice(1);
      const next = snapshot[0];
      if (next) {
        setNextIdea(next.idea);
        setNextToken(next.token);
      } else {
        const idea = await fetchIdeaFromAnthropic();
        const token = await prepareGame(idea);
        setQueue([{ idea, token }]);
        setNextIdea(idea);
        setNextToken(token);
      }
      while (queue.length < 3) {
        const idea = await fetchIdeaFromAnthropic();
        const token = await prepareGame(idea);
        setQueue((prev) => [...prev, { idea, token }]);
      }
    }, 0);
  };

  const handleNextClick = () => {
    if (isGeneratingRef.current || isSwiping) return;
    setIsSwiping(true);
    // Small visual swipe animation before triggering
    setTimeout(() => {
      const idea = nextIdea || generateIdeaLocally();
      if (nextToken) {
        applyPrepared(nextToken, idea).finally(() => rotateAndTopUpQueue());
      } else {
        updateGameViaFreestyle(idea).finally(() => rotateAndTopUpQueue());
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
