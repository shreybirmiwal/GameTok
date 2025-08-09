import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import GameZone from './GameZone';

function App() {
  const [currentGame, setCurrentGame] = useState("Your Game");
  const [gameInput, setGameInput] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectStatus, setConnectStatus] = useState("");

  // History of generated games
  const [gameHistory, setGameHistory] = useState(() => {
    try {
      const raw = localStorage.getItem('gameHistory');
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });

  // Pending pre-generated ideas queue
  const [preGenQueue, setPreGenQueue] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  const sentinelRef = useRef(null);
  const isGeneratingRef = useRef(false);

  useEffect(() => {
    localStorage.setItem('gameHistory', JSON.stringify(gameHistory));
  }, [gameHistory]);

  const updateGameViaFreestyle = async (gameName, options = { silent: false }) => {
    const { silent } = options;
    try {
      console.log(`Generating game: ${gameName} ${silent ? '(silent)' : ''}`);
      if (!silent) {
        setIsGenerating(true);
        setCurrentGame(`Generating ${gameName}...`);
      }
      isGeneratingRef.current = true;

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
        if (!silent) setCurrentGame(gameName);
        setGameHistory((prev) => [
          { id: Date.now(), idea: gameName, meta: { createdAt: new Date().toISOString(), result } },
          ...prev,
        ]);
      } else {
        const error = await response.json();
        console.error('Failed to generate game:', error);
        if (!silent) setCurrentGame(`Failed to generate ${gameName}`);
      }
    } catch (error) {
      console.error('Error calling game generation API:', error);
      if (!silent) setCurrentGame(`Error generating ${gameName}`);
    } finally {
      if (!silent) setIsGenerating(false);
      isGeneratingRef.current = false;
    }
  };

  const handleGameSubmit = (e) => {
    e.preventDefault();
    if (gameInput.trim()) {
      updateGameViaFreestyle(gameInput.trim());
      setGameInput("");
    }
  };

  const handleReconnect = async () => {
    try {
      setIsConnecting(true);
      setConnectStatus("Connecting...");
      const res = await fetch('http://localhost:8080/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (data.success) {
        setConnectStatus('Connected');
      } else {
        setConnectStatus(`Failed: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Reconnect error', err);
      setConnectStatus('Error connecting');
    } finally {
      setIsConnecting(false);
      setTimeout(() => setConnectStatus(""), 4000);
    }
  };

  // Export history as JSON file
  const handleExportHistory = () => {
    try {
      const blob = new Blob([JSON.stringify(gameHistory, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `game-history-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to export history', e);
    }
  };

  // Seed pre-generated ideas on mount for faster subsequent loads
  useEffect(() => {
    const seeds = [
      'Space Runner',
      'Jungle Jump',
      'Neon Racer',
      'Pixel Pirates',
      'Dungeon Dash',
      'Skyline Skater',
      'Astro Harvest',
      'Cyber Courier',
      'Robo Rally',
      'Mystic Merge',
    ];
    setPreGenQueue(seeds);

    // kick off a couple silently to warm the cache/history without changing current view
    const warm = async () => {
      const toWarm = seeds.slice(0, 2);
      for (const idea of toWarm) {
        await updateGameViaFreestyle(idea, { silent: true });
      }
    };
    warm();
  }, []);

  // Infinite scroll: when user scrolls near bottom, auto-generate next queued idea
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting) {
          if (!isGeneratingRef.current && preGenQueue.length > 0) {
            const [next, ...rest] = preGenQueue;
            setPreGenQueue(rest);
            updateGameViaFreestyle(next);
          }
        }
      },
      { root: null, rootMargin: '100px', threshold: 0 }
    );

    if (sentinelRef.current) observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [preGenQueue]);

  // Click a history item to go back to it
  const handleSelectHistory = (item) => {
    setCurrentGame(item.idea);
  };

  const historyEmpty = gameHistory.length === 0;

  return (
    <div className="App">
      <button
        onClick={handleReconnect}
        disabled={isConnecting}
        style={{
          position: 'fixed',
          top: 12,
          right: 12,
          zIndex: 1000,
          padding: '8px 12px',
          background: '#222',
          color: '#fff',
          border: '1px solid #444',
          borderRadius: 8,
          cursor: isConnecting ? 'not-allowed' : 'pointer'
        }}
        aria-label="Reconnect to dev server"
      >
        {isConnecting ? 'Reconnecting...' : 'Reconnect'}
      </button>
      {connectStatus && (
        <div style={{ position: 'fixed', top: 52, right: 12, zIndex: 1000, fontSize: 12, color: '#ccc' }}>
          {connectStatus}
        </div>
      )}

      <div className="content-container">
        <aside className="history-sidebar">
          <div className="history-header">
            <div className="history-title">Game History</div>
            <button className="export-button" onClick={handleExportHistory} disabled={historyEmpty}>
              Export JSON
            </button>
          </div>
          <div className="history-list">
            {historyEmpty ? (
              <div style={{ color: '#aaa', fontSize: 13 }}>No games yet</div>
            ) : (
              gameHistory.map((item) => (
                <div
                  key={item.id}
                  className="history-item"
                  onClick={() => handleSelectHistory(item)}
                  title={`Generated at ${item.meta?.createdAt || ''}`}
                >
                  {item.idea}
                </div>
              ))
            )}
          </div>
        </aside>

        <main className="main-area">
          <div className="game-input-section sticky-input">
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

          {/* Sentinel for infinite scroll */}
          <div ref={sentinelRef} className="scroll-sentinel" />
        </main>
      </div>

      {isGenerating && <div className="generate-status">Generating...</div>}
    </div>
  );
}

export default App;
