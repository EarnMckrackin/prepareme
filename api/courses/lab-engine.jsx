/* ============================================================
   LAB-ENGINE.JSX — Generic course rendering engine
   Renders any course data object into the learning experience.
   ============================================================ */
const { useState, useEffect, useRef, useCallback, useMemo } = React;

// ── Persistence ──────────────────────────────────────────────
const STORE_KEY = 'learning-lab-v1';
function loadState() {
  try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; } catch { return {}; }
}
function saveState(s) { localStorage.setItem(STORE_KEY, JSON.stringify(s)); }

function usePersist(courseId) {
  const [state, setState] = useState(() => {
    const all = loadState();
    return all[courseId] || { currentStage: 0, unlocked: [0], mastery: {}, drills: {}, lastAccessed: null };
  });
  useEffect(() => {
    const all = loadState();
    all[courseId] = { ...state, lastAccessed: Date.now() };
    saveState(all);
  }, [state, courseId]);
  const update = useCallback((fn) => setState(prev => {
    const next = typeof fn === 'function' ? fn(prev) : { ...prev, ...fn };
    return next;
  }), []);
  return [state, update];
}

// ── Progress Ring ────────────────────────────────────────────
function ProgressRing({ size = 40, stroke = 3, progress = 0, color = 'var(--accent)' }) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (progress * circ);
  return (
    <svg width={size} height={size} className="progress-ring">
      <circle className="progress-ring__bg" cx={size/2} cy={size/2} r={r}
        fill="none" strokeWidth={stroke} />
      <circle className="progress-ring__fill" cx={size/2} cy={size/2} r={r}
        fill="none" strokeWidth={stroke} style={{ stroke: color, strokeDasharray: circ, strokeDashoffset: offset }} />
    </svg>
  );
}

// ── Journey Spine ────────────────────────────────────────────
function JourneySpine({ stages, currentStage, unlocked, mastery, onSelect }) {
  return (
    <nav style={{
      display: 'flex', flexDirection: 'column', gap: 0,
      padding: '24px 0', width: 220, flexShrink: 0,
      borderRight: '1px solid var(--border)',
      background: 'var(--bg-base)',
      position: 'sticky', top: 0, height: '100vh',
      overflowY: 'auto',
    }}>
      <div style={{ padding: '0 20px 20px', borderBottom: '1px solid var(--border)' }}>
        <div className="eyebrow" style={{ marginBottom: 4 }}>Module Progress</div>
        <StageProgressBar stages={stages} mastery={mastery} />
      </div>
      <div style={{ padding: '12px 0', flex: 1 }}>
        {stages.map((stage, i) => {
          const isUnlocked = unlocked.includes(i);
          const isCurrent = currentStage === i;
          const conceptIds = stage.concepts.map(c => c.id);
          const masteredCount = conceptIds.filter(id => mastery[id] === 'mastered').length;
          const allMastered = masteredCount === conceptIds.length && conceptIds.length > 0;
          return (
            <button key={stage.id} onClick={() => isUnlocked && onSelect(i)}
              style={{
                display: 'flex', alignItems: 'flex-start', gap: 12,
                width: '100%', padding: '10px 20px', border: 'none',
                background: isCurrent ? 'var(--accent-soft)' : 'transparent',
                borderLeft: isCurrent ? '3px solid var(--accent)' : '3px solid transparent',
                cursor: isUnlocked ? 'pointer' : 'default',
                opacity: isUnlocked ? 1 : 0.35,
                textAlign: 'left',
                transition: 'all 150ms',
              }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                display: 'grid', placeItems: 'center',
                fontSize: 14,
                background: allMastered ? 'var(--success-soft)' : isCurrent ? 'var(--accent-soft)' : 'var(--bg-elevated)',
                border: `2px solid ${allMastered ? 'var(--success)' : isCurrent ? 'var(--accent)' : 'var(--border)'}`,
                color: allMastered ? 'var(--success)' : isCurrent ? 'var(--accent)' : 'var(--text-3)',
              }}>
                {allMastered ? '✓' : isUnlocked ? stage.icon : '🔒'}
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{
                  fontSize: 13, fontWeight: 600,
                  color: isCurrent ? 'var(--text-1)' : 'var(--text-2)',
                  lineHeight: 1.3,
                }}>{stage.title}</div>
                <div style={{
                  fontSize: 11, color: 'var(--text-3)', marginTop: 2,
                  fontFamily: 'var(--font-mono)',
                }}>{masteredCount}/{conceptIds.length} concepts</div>
              </div>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function StageProgressBar({ stages, mastery }) {
  const total = stages.reduce((sum, s) => sum + s.concepts.length, 0);
  const mastered = Object.values(mastery).filter(v => v === 'mastered').length;
  const learning = Object.values(mastery).filter(v => v === 'learning').length;
  const pct = total > 0 ? mastered / total : 0;
  return (
    <div>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        marginBottom: 6,
      }}>
        <span style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text-1)' }}>
          {Math.round(pct * 100)}%
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
          {mastered} mastered · {learning} learning
        </span>
      </div>
      <div style={{
        height: 6, borderRadius: 3, background: 'var(--bg-elevated)', overflow: 'hidden',
        display: 'flex',
      }}>
        <div style={{ width: `${(mastered/total)*100}%`, background: 'var(--success)', transition: 'width 400ms ease-out', borderRadius: 3 }}></div>
        <div style={{ width: `${(learning/total)*100}%`, background: 'var(--warm)', transition: 'width 400ms ease-out' }}></div>
      </div>
    </div>
  );
}

// ── Mobile Stage Nav ─────────────────────────────────────────
function MobileStageNav({ stages, currentStage, unlocked, mastery, onSelect }) {
  return (
    <div style={{
      display: 'flex', gap: 4, padding: '12px 16px',
      overflowX: 'auto', borderBottom: '1px solid var(--border)',
      background: 'var(--bg-base)',
    }}>
      {stages.map((stage, i) => {
        const isUnlocked = unlocked.includes(i);
        const isCurrent = currentStage === i;
        const conceptIds = stage.concepts.map(c => c.id);
        const allMastered = conceptIds.every(id => mastery[id] === 'mastered') && conceptIds.length > 0;
        return (
          <button key={stage.id} onClick={() => isUnlocked && onSelect(i)}
            style={{
              padding: '6px 14px', borderRadius: 'var(--r-pill)',
              border: `1px solid ${isCurrent ? 'var(--accent)' : 'var(--border)'}`,
              background: isCurrent ? 'var(--accent-soft)' : 'transparent',
              color: allMastered ? 'var(--success)' : isCurrent ? 'var(--accent)' : 'var(--text-3)',
              fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap',
              cursor: isUnlocked ? 'pointer' : 'default',
              opacity: isUnlocked ? 1 : 0.35,
              fontFamily: 'var(--font-body)',
            }}>
            {allMastered ? '✓ ' : ''}{stage.title}
          </button>
        );
      })}
    </div>
  );
}

// ── Stage View ───────────────────────────────────────────────
function StageView({ stage, stageIndex, totalStages, mastery, drills, onMastery, onDrill, onNext, isLast }) {
  const allDrillsAttempted = stage.concepts.every(c => drills[c.id]?.attempted);
  return (
    <div className="fade-up" style={{ maxWidth: 760, margin: '0 auto', padding: '32px 24px 80px' }}>
      {/* Stage header */}
      <div style={{ marginBottom: 40 }}>
        <div className="eyebrow" style={{ color: 'var(--accent)', marginBottom: 8 }}>
          Stage {stageIndex + 1} of {totalStages} — {stage.subtitle}
        </div>
        <h1 style={{ fontSize: 32, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12 }}>
          {stage.icon} {stage.title}
        </h1>
        <p style={{ fontSize: 15, color: 'var(--text-2)', lineHeight: 1.7, maxWidth: 640 }}>
          {stage.why}
        </p>
        <div style={{
          display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap',
        }}>
          {stage.concepts.map(c => (
            <ConceptPill key={c.id} concept={c} mastery={mastery[c.id] || 'unknown'} />
          ))}
        </div>
      </div>

      {/* Concepts */}
      {stage.concepts.map((concept, ci) => (
        <ConceptBlock
          key={concept.id}
          concept={concept}
          index={ci}
          mastery={mastery[concept.id] || 'unknown'}
          drillState={drills[concept.id]}
          onMastery={onMastery}
          onDrill={onDrill}
        />
      ))}

      {/* Stage complete / next */}
      <div style={{
        marginTop: 48, padding: 32, borderRadius: 'var(--r-lg)',
        background: allDrillsAttempted ? 'var(--success-soft)' : 'var(--bg-surface)',
        border: `1px solid ${allDrillsAttempted ? 'var(--success)' : 'var(--border)'}`,
        textAlign: 'center',
      }}>
        {allDrillsAttempted ? (
          <>
            <div style={{ fontSize: 24, marginBottom: 8 }}>✓</div>
            <h3 style={{ fontSize: 20, color: 'var(--success)', marginBottom: 8 }}>Stage Complete</h3>
            <p style={{ fontSize: 14, color: 'var(--text-2)', marginBottom: 20 }}>
              {isLast ? 'You\'ve completed this module. Return to the dashboard to see your progress.' : 'The next stage is now unlocked.'}
            </p>
            {!isLast && (
              <button className="pill-btn primary" onClick={onNext}>
                Continue to next stage →
              </button>
            )}
          </>
        ) : (
          <>
            <div style={{ fontSize: 24, marginBottom: 8, opacity: 0.4 }}>🔒</div>
            <h3 style={{ fontSize: 18, color: 'var(--text-2)', marginBottom: 8 }}>Complete All Drills to Continue</h3>
            <p style={{ fontSize: 13, color: 'var(--text-3)' }}>
              Attempt each drill above (you don't need to get them all right — just try each one).
            </p>
          </>
        )}
      </div>
    </div>
  );
}

function ConceptPill({ concept, mastery }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '4px 10px', borderRadius: 'var(--r-pill)',
      background: mastery === 'mastered' ? 'var(--success-soft)' : mastery === 'learning' ? 'var(--warm-soft)' : 'var(--bg-elevated)',
      border: `1px solid ${mastery === 'mastered' ? 'rgba(52,211,153,.2)' : mastery === 'learning' ? 'rgba(240,160,48,.2)' : 'var(--border)'}`,
      fontSize: 11, fontWeight: 600,
      color: mastery === 'mastered' ? 'var(--success)' : mastery === 'learning' ? 'var(--warm)' : 'var(--text-3)',
    }}>
      <span className={`mastery-dot ${mastery}`}></span>
      {concept.title}
    </div>
  );
}

// ── Concept Block ────────────────────────────────────────────
function ConceptBlock({ concept, index, mastery, drillState, onMastery, onDrill }) {
  const [expanded, setExpanded] = useState(true);
  const c = concept;
  return (
    <section style={{
      marginBottom: 40,
      borderLeft: `3px solid ${mastery === 'mastered' ? 'var(--success)' : mastery === 'learning' ? 'var(--warm)' : 'var(--border)'}`,
      paddingLeft: 24,
      transition: 'border-color 300ms',
    }}>
      {/* Concept header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
        cursor: 'pointer',
      }} onClick={() => setExpanded(!expanded)}>
        <span className={`mastery-dot ${mastery}`} style={{ width: 10, height: 10 }}></span>
        <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-1)', flex: 1 }}>
          {c.title}
        </h2>
        <span style={{ fontSize: 12, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
          {mastery === 'mastered' ? 'MASTERED' : mastery === 'learning' ? 'LEARNING' : ''}
        </span>
        <span style={{ color: 'var(--text-3)', fontSize: 14, transition: 'transform 200ms', transform: expanded ? 'rotate(0)' : 'rotate(-90deg)' }}>▼</span>
      </div>

      {expanded && (
        <div className="fade-in">
          {/* WHY — the scenario */}
          <div style={{
            background: 'var(--accent-soft)', borderRadius: 'var(--r-md)',
            padding: '16px 20px', marginBottom: 20,
            borderLeft: '3px solid var(--accent)',
          }}>
            <div className="eyebrow" style={{ color: 'var(--accent)', marginBottom: 8 }}>Why this matters</div>
            <p style={{ fontSize: 14, color: 'var(--text-1)', lineHeight: 1.7, fontStyle: 'italic' }}>
              {c.why.scenario}
            </p>
            {c.why.tension && (
              <p style={{ fontSize: 13, color: 'var(--warm)', marginTop: 8, fontWeight: 600 }}>
                ↳ {c.why.tension}
              </p>
            )}
          </div>

          {/* WHAT — definition(s) */}
          <DefinitionCard def={c.what} />
          {c.what2 && <DefinitionCard def={c.what2} />}

          {/* EXAMPLE */}
          {c.example && <ExampleBlock example={c.example} />}

          {/* DRILL */}
          {c.drill && (
            <DrillBlock
              conceptId={c.id}
              drill={c.drill}
              state={drillState}
              mastery={mastery}
              onDrill={onDrill}
              onMastery={onMastery}
            />
          )}
        </div>
      )}
    </section>
  );
}

function DefinitionCard({ def }) {
  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border)',
      borderRadius: 'var(--r-md)', padding: '16px 20px', marginBottom: 16,
    }}>
      <div className="eyebrow" style={{ color: 'var(--info)', marginBottom: 6 }}>{def.definition}</div>
      <p style={{ fontSize: 14, color: 'var(--text-2)', lineHeight: 1.75 }}
        dangerouslySetInnerHTML={{ __html: formatBold(def.body) }} />
    </div>
  );
}

function formatBold(text) {
  let out = text.replace(/\*\*(.+?)\*\*/g, '<strong style="color:var(--text-1);font-weight:600">$1</strong>');
  out = out.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em style="color:var(--text-1)">$1</em>');
  return out;
}

// ── Example Block ────────────────────────────────────────────
function ExampleBlock({ example }) {
  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border)',
      borderRadius: 'var(--r-md)', padding: '16px 20px', marginBottom: 16,
    }}>
      <div className="eyebrow" style={{ color: 'var(--warm)', marginBottom: 12 }}>{example.label}</div>

      {/* Spectrum items */}
      {example.items && !example.code && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {example.items.map((item, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '10px 14px', borderRadius: 'var(--r-sm)',
              background: 'var(--bg-elevated)',
            }}>
              <span style={{ fontSize: 18, flexShrink: 0 }}>{item.icon}</span>
              <div style={{ flex: 1 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-1)' }}>{item.left}</span>
                <span style={{ fontSize: 12, color: 'var(--text-3)', marginLeft: 8 }}>— {item.right}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      {example.table && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr>
                <th style={thStyle}>Scenario</th>
                <th style={thStyle}>Lever</th>
                <th style={thStyle}>Why</th>
              </tr>
            </thead>
            <tbody>
              {example.table.map((row, i) => (
                <tr key={i}>
                  <td style={tdStyle}>{row.scenario}</td>
                  <td style={{...tdStyle, fontWeight: 600, color: row.fix === 'Fine-tune' ? 'var(--accent)' : 'var(--info)' }}>{row.fix}</td>
                  <td style={{...tdStyle, color: 'var(--text-3)'}}>{row.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Code block */}
      {example.code && example.codeContent && (
        <pre className="code-block" style={{ margin: 0 }}>
          {example.codeContent.map((token, i) => (
            <span key={i} className={token.cls || ''}>{token.text}</span>
          ))}
        </pre>
      )}

      {/* Comparison */}
      {example.comparison && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div style={{ padding: 14, borderRadius: 'var(--r-sm)', background: 'var(--error-soft)', border: '1px solid rgba(248,113,113,.15)' }}>
            <div className="eyebrow" style={{ color: 'var(--error)', marginBottom: 8 }}>{example.comparison.bad.label}</div>
            <pre style={{ fontSize: 11, color: 'var(--text-2)', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', lineHeight: 1.6 }}>
              {example.comparison.bad.content}
            </pre>
          </div>
          <div style={{ padding: 14, borderRadius: 'var(--r-sm)', background: 'var(--success-soft)', border: '1px solid rgba(52,211,153,.15)' }}>
            <div className="eyebrow" style={{ color: 'var(--success)', marginBottom: 8 }}>{example.comparison.good.label}</div>
            <pre style={{ fontSize: 11, color: 'var(--text-2)', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', lineHeight: 1.6 }}>
              {example.comparison.good.content}
            </pre>
          </div>
        </div>
      )}

      {/* Costs table */}
      {example.costs && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {example.costs.map((row, i) => (
            <div key={i} style={{
              display: 'grid', gridTemplateColumns: '1fr auto auto', gap: 16,
              padding: '8px 12px', borderRadius: 'var(--r-sm)',
              background: i % 2 === 0 ? 'var(--bg-elevated)' : 'transparent',
              fontSize: 13,
            }}>
              <span style={{ color: 'var(--text-1)' }}>{row.item}</span>
              <span style={{ color: 'var(--text-3)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>{row.time}</span>
              <span style={{ color: 'var(--warm)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>{row.cost}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const thStyle = {
  textAlign: 'left', padding: '8px 12px',
  borderBottom: '1px solid var(--border)',
  color: 'var(--text-3)', fontWeight: 600, fontSize: 11,
  fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '.05em',
};
const tdStyle = {
  padding: '10px 12px', borderBottom: '1px solid var(--border)',
  color: 'var(--text-2)', lineHeight: 1.5,
};

// ── Drill Block ──────────────────────────────────────────────
function DrillBlock({ conceptId, drill, state, mastery, onDrill, onMastery }) {
  const [selected, setSelected] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [matchAnswers, setMatchAnswers] = useState({});
  const [matchChecked, setMatchChecked] = useState(false);
  const isCorrect = drill.type === 'match'
    ? (drill.pairs || []).every(p => matchAnswers[p.item] === p.answer)
    : selected === drill.correct;

  const handleConfirm = () => {
    setConfirmed(true);
    const correct = drill.type === 'match'
      ? (drill.pairs || []).every(p => matchAnswers[p.item] === p.answer)
      : selected === drill.correct;
    onDrill(conceptId, { attempted: true, correct });
    if (correct && mastery !== 'mastered') {
      onMastery(conceptId, 'mastered');
    } else if (!correct && mastery === 'unknown') {
      onMastery(conceptId, 'learning');
    }
  };

  const handleRetry = () => {
    setSelected(null);
    setConfirmed(false);
    setMatchAnswers({});
    setMatchChecked(false);
  };

  return (
    <div style={{
      background: 'var(--bg-deep)', border: '1px solid var(--border)',
      borderRadius: 'var(--r-lg)', padding: '20px 24px', marginBottom: 16,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <span style={{
          padding: '3px 10px', borderRadius: 'var(--r-pill)',
          background: 'var(--accent-soft)', color: 'var(--accent)',
          fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)',
          letterSpacing: '.04em', textTransform: 'uppercase',
          whiteSpace: 'nowrap',
        }}>Try it</span>
        {state?.attempted && (
          <span style={{
            padding: '3px 10px', borderRadius: 'var(--r-pill)',
            background: state.correct ? 'var(--success-soft)' : 'var(--warm-soft)',
            color: state.correct ? 'var(--success)' : 'var(--warm)',
            fontSize: 11, fontWeight: 600, fontFamily: 'var(--font-mono)',
          }}>{state.correct ? '✓ Correct' : '~ Attempted'}</span>
        )}
      </div>

      <p style={{ fontSize: 14, color: 'var(--text-1)', lineHeight: 1.7, marginBottom: 16, whiteSpace: 'pre-line' }}>
        {drill.question}
      </p>

      {/* Choice / Scenario drill */}
      {(drill.type === 'choice' || drill.type === 'scenario') && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {(drill.options || []).map((opt, i) => {
            const isOpt = typeof opt === 'string';
            const label = isOpt ? opt : opt.label;
            const detail = isOpt ? null : opt.detail;
            const isSelected = selected === i;
            const isCorrectOpt = i === drill.correct;
            let bg = 'var(--bg-surface)';
            let border = 'var(--border)';
            let labelColor = 'var(--text-1)';
            if (confirmed && isCorrectOpt) { bg = 'var(--success-soft)'; border = 'var(--success)'; labelColor = 'var(--success)'; }
            else if (confirmed && isSelected && !isCorrectOpt) { bg = 'var(--error-soft)'; border = 'var(--error)'; labelColor = 'var(--error)'; }
            else if (confirmed) { bg = 'var(--bg-surface)'; border = 'var(--border)'; labelColor = 'var(--text-3)'; }
            else if (isSelected) { bg = 'var(--accent-soft)'; border = 'var(--accent)'; }
            return (
              <button key={i} onClick={() => !confirmed && setSelected(i)}
                disabled={confirmed}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: 10,
                  padding: '12px 16px', borderRadius: 'var(--r-md)',
                  background: bg, border: `1px solid ${border}`,
                  cursor: confirmed ? 'default' : 'pointer',
                  textAlign: 'left', transition: 'all 150ms',
                  fontFamily: 'var(--font-body)',
                }}>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700,
                  color: confirmed && isCorrectOpt ? 'var(--success)' : confirmed && isSelected ? 'var(--error)' : 'var(--text-3)',
                  flexShrink: 0, marginTop: 1,
                }}>{'ABCD'[i]}.</span>
                <div>
                  <span style={{ fontSize: 13, color: labelColor, lineHeight: 1.6 }}>{label}</span>
                  {detail && <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 4, lineHeight: 1.5 }}>{detail}</div>}
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Match drill */}
      {drill.type === 'match' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {(drill.pairs || []).map((pair, i) => {
            const answers = [...new Set(drill.pairs.map(p => p.answer))];
            const chosen = matchAnswers[pair.item];
            const isRight = confirmed && chosen === pair.answer;
            const isWrong = confirmed && chosen && chosen !== pair.answer;
            return (
              <div key={i} style={{
                padding: '12px 16px', borderRadius: 'var(--r-md)',
                background: isRight ? 'var(--success-soft)' : isWrong ? 'var(--error-soft)' : 'var(--bg-surface)',
                border: `1px solid ${isRight ? 'var(--success)' : isWrong ? 'var(--error)' : 'var(--border)'}`,
              }}>
                <div style={{ fontSize: 13, color: 'var(--text-1)', marginBottom: 8 }}>{pair.item}</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {answers.map(a => (
                    <button key={a} onClick={() => !confirmed && setMatchAnswers(prev => ({...prev, [pair.item]: a}))}
                      disabled={confirmed}
                      style={{
                        padding: '4px 12px', borderRadius: 'var(--r-pill)', fontSize: 12, fontWeight: 600,
                        background: chosen === a ? 'var(--accent-soft)' : 'var(--bg-elevated)',
                        border: `1px solid ${chosen === a ? 'var(--accent)' : 'var(--border)'}`,
                        color: chosen === a ? 'var(--accent)' : 'var(--text-2)',
                        cursor: confirmed ? 'default' : 'pointer',
                        fontFamily: 'var(--font-body)',
                      }}>{a}</button>
                  ))}
                </div>
                {isWrong && <div style={{ fontSize: 11, color: 'var(--success)', marginTop: 6 }}>→ {pair.answer}</div>}
              </div>
            );
          })}
        </div>
      )}

      {/* Confirm / Explanation */}
      <div style={{ marginTop: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
        {!confirmed && (
          <button className="pill-btn primary sm"
            disabled={drill.type === 'match' ? Object.keys(matchAnswers).length < (drill.pairs || []).length : selected === null}
            onClick={handleConfirm}>
            Check answer
          </button>
        )}
        {confirmed && !isCorrect && (
          <button className="pill-btn sm" onClick={handleRetry}>Try again</button>
        )}
      </div>

      {confirmed && (
        <div className="fade-in" style={{
          marginTop: 14, padding: '14px 18px', borderRadius: 'var(--r-md)',
          background: isCorrect ? 'var(--success-soft)' : 'var(--warm-soft)',
          borderLeft: `3px solid ${isCorrect ? 'var(--success)' : 'var(--warm)'}`,
        }}>
          <div className="eyebrow" style={{ color: isCorrect ? 'var(--success)' : 'var(--warm)', marginBottom: 6 }}>
            {isCorrect ? '✓ Correct' : '✗ Not quite'}
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7 }}>
            {drill.explanation}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Export ────────────────────────────────────────────────────
window.ProgressRing = ProgressRing;
window.JourneySpine = JourneySpine;
window.MobileStageNav = MobileStageNav;
window.StageView = StageView;
window.StageProgressBar = StageProgressBar;
window.usePersist = usePersist;
window.loadState = loadState;
