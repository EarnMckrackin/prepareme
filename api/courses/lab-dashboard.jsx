/* ============================================================
   LAB-DASHBOARD.JSX — Library dashboard with progress + suggestions
   ============================================================ */

function Dashboard({ courses, onOpenCourse, allState }) {
  const config = window.LAB_CONFIG || {
    brand: 'Learning Lab',
    title: 'Your courses',
    description: 'Master Gen AI concepts through doing. Each module builds on the last — learn the concept, see it in action, then prove you understand.',
    eyebrow: 'Advanced RAG & Agentic Systems — Level 2',
    nextEyebrow: "What's next",
    nextTitle: 'Start with Fine-Tuning',
    nextBody: 'Module A is the foundation — it teaches you when to improve the model itself vs. improving what you feed it. Complete it to unlock personalized recommendations for your next module.',
    nextCourseId: 'fine-tuning',
    nextCta: 'Begin Module A →',
  };
  const completedIds = [];
  courses.forEach(course => {
    if (course.stages && course.stages.length > 0) {
      const st = allState[course.id];
      if (st) {
        const total = course.stages.reduce((s, stg) => s + stg.concepts.length, 0);
        const mastered = Object.values(st.mastery || {}).filter(v => v === 'mastered').length;
        if (mastered === total && total > 0) completedIds.push(course.id);
      }
    }
  });

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-deep)' }}>
      {/* Hero header */}
      <header style={{
        padding: '48px 32px 40px', maxWidth: 960, margin: '0 auto',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 'var(--r-md)',
            background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
            display: 'grid', placeItems: 'center',
            fontSize: 18, fontWeight: 700, color: '#fff',
          }}>L</div>
          <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-1)', letterSpacing: '-.01em' }}>
            {config.brand}
          </span>
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 700,
          color: 'var(--text-1)', lineHeight: 1.2, marginBottom: 8,
        }}>
          {config.title}
        </h1>
        <p style={{ fontSize: 15, color: 'var(--text-2)', maxWidth: 520 }}>
          {config.description}
        </p>
      </header>

      <main style={{ maxWidth: 960, margin: '0 auto', padding: '0 32px 80px' }}>
        {/* Overall progress */}
        <OverallProgress courses={courses} allState={allState} />

        {/* Course grid */}
        <section style={{ marginTop: 40 }}>
          <div className="eyebrow" style={{ marginBottom: 16, color: 'var(--text-3)' }}>
            {config.eyebrow}
          </div>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: 16,
          }}>
            {courses.map(course => (
              <CourseCard
                key={course.id}
                course={course}
                state={allState[course.id]}
                onOpen={() => onOpenCourse(course.id)}
              />
            ))}
          </div>
        </section>

        {/* Upload section */}
        <section style={{ marginTop: 48 }}>
          <UploadSection />
        </section>

        {/* Suggestions */}
        {completedIds.length > 0 && (
          <section style={{ marginTop: 48 }}>
            <SuggestionsPanel completedIds={completedIds} />
          </section>
        )}

        {/* What's next even without completions */}
        {completedIds.length === 0 && (
          <section style={{ marginTop: 48 }}>
            <div style={{
              padding: 28, borderRadius: 'var(--r-lg)',
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
            }}>
              <div className="eyebrow" style={{ color: 'var(--warm)', marginBottom: 8 }}>{config.nextEyebrow}</div>
              <h3 style={{ fontSize: 18, color: 'var(--text-1)', marginBottom: 8 }}>
                {config.nextTitle}
              </h3>
              <p style={{ fontSize: 14, color: 'var(--text-2)', lineHeight: 1.7, marginBottom: 16 }}>
                {config.nextBody}
              </p>
              <button className="pill-btn primary" onClick={() => onOpenCourse(config.nextCourseId)}>
                {config.nextCta}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function OverallProgress({ courses, allState }) {
  let totalConcepts = 0, mastered = 0, learning = 0, modulesStarted = 0;
  courses.forEach(c => {
    if (!c.stages) return;
    const concepts = c.stages.reduce((s, stg) => s + stg.concepts.length, 0);
    totalConcepts += concepts;
    const st = allState[c.id];
    if (st && st.mastery) {
      const m = Object.values(st.mastery).filter(v => v === 'mastered').length;
      const l = Object.values(st.mastery).filter(v => v === 'learning').length;
      mastered += m;
      learning += l;
      if (m + l > 0) modulesStarted++;
    }
  });
  if (totalConcepts === 0) return null;
  const pct = Math.round((mastered / totalConcepts) * 100);

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16,
    }}>
      {[
        { label: 'Overall', value: `${pct}%`, sub: 'mastery', color: 'var(--accent)' },
        { label: 'Concepts', value: `${mastered}/${totalConcepts}`, sub: 'mastered', color: 'var(--success)' },
        { label: 'In progress', value: learning, sub: 'learning', color: 'var(--warm)' },
        { label: 'Modules', value: `${modulesStarted}/${courses.length}`, sub: 'started', color: 'var(--info)' },
      ].map((stat, i) => (
        <div key={i} style={{
          padding: '18px 20px', borderRadius: 'var(--r-md)',
          background: 'var(--bg-surface)', border: '1px solid var(--border)',
        }}>
          <div className="eyebrow" style={{ marginBottom: 6 }}>{stat.label}</div>
          <div style={{
            fontSize: 28, fontWeight: 700, fontFamily: 'var(--font-display)',
            color: stat.color, lineHeight: 1,
          }}>{stat.value}</div>
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 4 }}>{stat.sub}</div>
        </div>
      ))}
    </div>
  );
}

function CourseCard({ course, state, onOpen }) {
  const isLocked = course.locked;
  const hasStages = course.stages && course.stages.length > 0;
  const total = hasStages ? course.stages.reduce((s, stg) => s + stg.concepts.length, 0) : 0;
  const mastered = state ? Object.values(state.mastery || {}).filter(v => v === 'mastered').length : 0;
  const learning = state ? Object.values(state.mastery || {}).filter(v => v === 'learning').length : 0;
  const started = mastered + learning > 0;
  const complete = mastered === total && total > 0;
  const pct = total > 0 ? mastered / total : 0;

  const stagesComplete = state ? (state.unlocked || [0]).length - 1 : 0;
  const totalStages = hasStages ? course.stages.length : 0;

  return (
    <div
      onClick={() => !isLocked && hasStages && onOpen()}
      style={{
        padding: 24, borderRadius: 'var(--r-lg)',
        background: 'var(--bg-surface)', border: `1px solid ${complete ? 'var(--success)' : 'var(--border)'}`,
        cursor: isLocked ? 'default' : 'pointer',
        opacity: isLocked ? 0.4 : 1,
        transition: 'all 180ms',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={e => { if (!isLocked) { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.background = 'var(--bg-elevated)'; }}}
      onMouseLeave={e => { e.currentTarget.style.borderColor = complete ? 'var(--success)' : 'var(--border)'; e.currentTarget.style.background = 'var(--bg-surface)'; }}
    >
      {/* Module label */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <span style={{
          padding: '4px 10px', borderRadius: 'var(--r-pill)',
          background: complete ? 'var(--success-soft)' : 'var(--accent-soft)',
          color: complete ? 'var(--success)' : 'var(--accent)',
          fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)',
        }}>
          {isLocked ? '🔒 ' : ''}{complete ? '✓ ' : ''}Module {course.moduleLabel}
        </span>
        {started && !isLocked && (
          <ProgressRing size={32} stroke={3} progress={pct}
            color={complete ? 'var(--success)' : 'var(--accent)'} />
        )}
      </div>

      <h3 style={{ fontSize: 17, fontWeight: 700, color: 'var(--text-1)', marginBottom: 8, lineHeight: 1.3 }}>
        {course.title}
      </h3>
      <p style={{ fontSize: 13, color: 'var(--text-3)', lineHeight: 1.6, marginBottom: 16 }}>
        {course.description}
      </p>

      {/* Tags */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 16 }}>
        {(course.tags || []).slice(0, 4).map(tag => (
          <span key={tag} style={{
            padding: '2px 8px', borderRadius: 'var(--r-pill)',
            background: 'var(--bg-elevated)', fontSize: 11,
            color: 'var(--text-3)', fontFamily: 'var(--font-mono)',
          }}>{tag}</span>
        ))}
      </div>

      {/* Progress footer */}
      {hasStages && !isLocked && (
        <div>
          <div style={{
            height: 4, borderRadius: 2, background: 'var(--bg-elevated)',
            overflow: 'hidden', marginBottom: 8,
          }}>
            <div style={{
              height: '100%', borderRadius: 2,
              width: `${pct * 100}%`,
              background: complete ? 'var(--success)' : 'var(--accent)',
              transition: 'width 400ms ease-out',
            }}></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--text-3)' }}>
              {started ? `${mastered}/${total} concepts` : 'Not started'}
            </span>
            <span style={{ color: 'var(--text-3)' }}>
              {totalStages} stages
            </span>
          </div>
        </div>
      )}

      {isLocked && (
        <div style={{ fontSize: 12, color: 'var(--text-3)', fontStyle: 'italic' }}>
          Coming soon — complete Module A first
        </div>
      )}
    </div>
  );
}

function UploadSection() {
  const [hover, setHover] = React.useState(false);
  return (
    <div style={{
      padding: 32, borderRadius: 'var(--r-lg)',
      border: `2px dashed ${hover ? 'var(--accent)' : 'var(--border)'}`,
      background: hover ? 'var(--accent-soft)' : 'transparent',
      textAlign: 'center', transition: 'all 200ms',
      cursor: 'pointer',
    }}
      onDragOver={e => { e.preventDefault(); setHover(true); }}
      onDragLeave={() => setHover(false)}
      onDrop={e => { e.preventDefault(); setHover(false); alert('Upload received! In production, this sends the HTML to the conversion pipeline.'); }}
      onClick={() => alert('In production, this opens a file picker and sends the HTML to the LLM conversion pipeline (PrepareMe backend). The engine converts any existing course into this enhanced learning format.')}
    >
      <div style={{ fontSize: 32, marginBottom: 8, opacity: 0.5 }}>📄</div>
      <h3 style={{ fontSize: 16, color: 'var(--text-1)', marginBottom: 6 }}>
        Import an existing course
      </h3>
      <p style={{ fontSize: 13, color: 'var(--text-3)', maxWidth: 400, margin: '0 auto', lineHeight: 1.6 }}>
        Drop an HTML learning tool here to convert it into the enhanced format with interactive drills, mastery tracking, and the full learning experience.
      </p>
      <div style={{
        marginTop: 12, padding: '4px 12px', borderRadius: 'var(--r-pill)',
        background: 'var(--bg-elevated)', display: 'inline-block',
        fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--font-mono)',
      }}>Requires PrepareMe backend</div>
    </div>
  );
}

function SuggestionsPanel({ completedIds }) {
  const suggestions = (window.SUGGESTED_NEXT || []).filter(s => completedIds.includes(s.prereq));
  if (suggestions.length === 0) return null;
  return (
    <div>
      <div className="eyebrow" style={{ color: 'var(--warm)', marginBottom: 16 }}>
        Recommended next
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {suggestions.map((s, i) => (
          <div key={i} style={{
            padding: '20px 24px', borderRadius: 'var(--r-md)',
            background: 'var(--warm-soft)', border: '1px solid rgba(240,160,48,.15)',
            display: 'flex', alignItems: 'flex-start', gap: 16,
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
              background: 'var(--warm-soft)', border: '2px solid var(--warm)',
              display: 'grid', placeItems: 'center',
              fontSize: 14, fontWeight: 700, color: 'var(--warm)',
              fontFamily: 'var(--font-mono)',
            }}>{s.moduleLabel}</div>
            <div>
              <h4 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-1)', marginBottom: 4 }}>{s.title}</h4>
              <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6 }}>{s.reason}</p>
              <div style={{
                marginTop: 8, fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--font-mono)',
              }}>Level {s.level} · Coming soon</div>
            </div>
          </div>
        ))}
        <div style={{
          padding: '16px 20px', borderRadius: 'var(--r-md)',
          background: 'var(--bg-surface)', border: '1px solid var(--border)',
          textAlign: 'center',
        }}>
          <p style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 4 }}>
            Want a course on a different topic?
          </p>
          <p style={{ fontSize: 12, color: 'var(--text-3)' }}>
            With PrepareMe, you can generate a full learning experience from any document or topic.
          </p>
        </div>
      </div>
    </div>
  );
}

window.Dashboard = Dashboard;
