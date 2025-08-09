import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const [currentGame, setCurrentGame] = useState('Your Game');
  const [gameInput, setGameInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastPrompt, setLastPrompt] = useState('');
  const [isSwiping, setIsSwiping] = useState(false);
  const [hasNextReady, setHasNextReady] = useState(false);
  const [prefetchCount, setPrefetchCount] = useState(0);

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

  // Helper: prefill the next-game slot on the server
  const fillNextSlot = async (idea) => {
    try {
      const res = await fetch('http://localhost:8080/fill-next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(idea ? { idea } : {}),
      });
      return await res.json();
    } catch (e) {
      console.warn('fill-next failed', e);
      return null;
    }
  };

  // Helper: try to instantly apply the cached next-game
  const applyNextIfReady = async () => {
    try {
      const res = await fetch('http://localhost:8080/scroll-apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const data = await res.json().catch(() => ({}));
      return { status: res.status, ok: res.ok, ...data };
    } catch (e) {
      return { ok: false, error: String(e) };
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

  const handleGameSubmit = async (e) => {
    e.preventDefault();
    const idea = gameInput.trim();
    if (!idea) return;
    setGameInput('');
    // Start prefill immediately in parallel with full generate
    fillNextSlot().catch(() => { });
    await updateGameViaFreestyle(idea);
    // After a full generate, prefill the next-game slot for fast scroll
    fillNextSlot().catch(() => { });
    // Top off to 5 in the background
    topOffPrefetch().catch(() => { });
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
        // Start prefill immediately in parallel with the first generate
        fillNextSlot().catch(() => { });
        await updateGameViaFreestyle(idea);
        // Prefill the next-game slot right after initial generate
        fillNextSlot().catch(() => { });
        // Top off to 5 in the background
        topOffPrefetch().catch(() => { });
      } catch (e) {
        console.warn('Auto-init failed', e);
      }
    })();
  }, []);

  const pollPreparedStatus = async () => {
    try {
      const res = await fetch('http://localhost:8080/prepared-status');
      if (!res.ok) return;
      const data = await res.json();
      setHasNextReady(Boolean(data?.has_next));
      setPrefetchCount(Number(data?.count || 0));
    } catch (e) {
      // ignore
    }
  };

  // Top-off prefetch queue to target size
  const topOffPrefetch = async (target = 5) => {
    try {
      // ask backend to fill up to 'target' by passing remaining count guess
      const remaining = Math.max(0, target - prefetchCount);
      if (remaining <= 0) return;
      await fetch('http://localhost:8080/fill-next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: remaining }),
      });
      // refresh status after top-off
      pollPreparedStatus();
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    // Poll readiness every few seconds
    const id = setInterval(pollPreparedStatus, 3000);
    pollPreparedStatus();
    return () => clearInterval(id);
  }, []);

  const handleNextClick = async () => {
    if (isGeneratingRef.current || isSwiping) return;
    setIsSwiping(true);
    setIsGenerating(true);
    isGeneratingRef.current = true;

    try {
      // 1) Try instant apply of cached next-game
      const applied = await applyNextIfReady();
      if (applied?.success && applied?.used_next) {
        const idea = applied.game_idea || 'next game';
        setLastPrompt(idea);
        setCurrentGame(`Loading ${idea}...`);
        // Reload to reflect written GameZone.js
        setTimeout(() => { try { window.location.reload(); } catch { } }, 150);
        // Refill the next slot in the background for the following scroll
        fillNextSlot().catch(() => { });
        // Top off after consuming one
        topOffPrefetch().catch(() => { });
        return;
      }

      // 2) Fallback: fetch idea then do full generate
      const idea = await fetchIdeaFromAnthropic();
      await updateGameViaFreestyle(idea);
      // Refill after full generate
      fillNextSlot().catch(() => { });
      // Top off in the background
      topOffPrefetch().catch(() => { });
    } catch (e) {
      console.warn('Next click flow failed', e);
    } finally {
      setIsGenerating(false);
      isGeneratingRef.current = false;
      setIsSwiping(false);
    }
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
          {hasNextReady && <span className="ready-dot" />}
        </button>
        <div style={{ fontSize: 10, opacity: 0.6, marginTop: 4 }}>
          Prefetched: {prefetchCount}
        </div>
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
