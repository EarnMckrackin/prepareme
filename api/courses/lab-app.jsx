/* ============================================================
   LAB-APP.JSX — Main app: routing, state, composition
   ============================================================ */

function App() {
  const [view, setView] = React.useState('dashboard'); // 'dashboard' | 'course'
  const [activeCourseId, setActiveCourseId] = React.useState(null);
  const [isMobile, setIsMobile] = React.useState(window.innerWidth < 768);

  React.useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Load all course states for the dashboard
  const allState = React.useMemo(() => loadState(), [view]);

  const handleOpenCourse = (courseId) => {
    setActiveCourseId(courseId);
    setView('course');
    window.scrollTo(0, 0);
  };

  const handleBackToDashboard = () => {
    setView('dashboard');
    setActiveCourseId(null);
    window.scrollTo(0, 0);
  };

  if (view === 'dashboard') {
    return (
      <Dashboard
        courses={LIBRARY_COURSES}
        allState={allState}
        onOpenCourse={handleOpenCourse}
      />
    );
  }

  const course = LIBRARY_COURSES.find(c => c.id === activeCourseId);
  if (!course || !course.stages || course.stages.length === 0) {
    return (
      <div style={{ padding: 60, textAlign: 'center' }}>
        <p style={{ color: 'var(--text-2)' }}>This module isn't available yet.</p>
        <button className="pill-btn" style={{ marginTop: 16 }} onClick={handleBackToDashboard}>
          ← Back to dashboard
        </button>
      </div>
    );
  }

  return (
    <CourseView
      course={course}
      isMobile={isMobile}
      onBack={handleBackToDashboard}
    />
  );
}

// ── Course View ──────────────────────────────────────────────
function CourseView({ course, isMobile, onBack }) {
  const [state, update] = usePersist(course.id);

  const setCurrentStage = (i) => {
    update(prev => ({ ...prev, currentStage: i }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleMastery = (conceptId, level) => {
    update(prev => ({
      ...prev,
      mastery: { ...prev.mastery, [conceptId]: level },
    }));
  };

  const handleDrill = (conceptId, result) => {
    update(prev => {
      const newDrills = { ...prev.drills, [conceptId]: result };
      // Check if all drills in current stage are attempted → unlock next
      const currentStageObj = course.stages[prev.currentStage];
      const allAttempted = currentStageObj.concepts.every(c => newDrills[c.id]?.attempted);
      let newUnlocked = [...prev.unlocked];
      if (allAttempted && prev.currentStage < course.stages.length - 1) {
        const nextIdx = prev.currentStage + 1;
        if (!newUnlocked.includes(nextIdx)) {
          newUnlocked = [...newUnlocked, nextIdx];
        }
      }
      return { ...prev, drills: newDrills, unlocked: newUnlocked };
    });
  };

  const handleNextStage = () => {
    const next = state.currentStage + 1;
    if (next < course.stages.length) {
      setCurrentStage(next);
    }
  };

  const currentStage = course.stages[state.currentStage];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Top bar */}
      <header style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 20px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-base)',
        position: 'sticky', top: 0, zIndex: 50,
      }}>
        <button onClick={onBack} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--text-3)', fontSize: 13, fontFamily: 'var(--font-body)',
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '6px 0',
        }}>
          <span style={{ fontSize: 16 }}>←</span> Library
        </button>
        <div style={{ width: 1, height: 18, background: 'var(--border)' }}></div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-1)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {course.title}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <MiniProgress course={course} mastery={state.mastery} />
        </div>
      </header>

      {/* Mobile nav */}
      {isMobile && (
        <MobileStageNav
          stages={course.stages}
          currentStage={state.currentStage}
          unlocked={state.unlocked}
          mastery={state.mastery}
          onSelect={setCurrentStage}
        />
      )}

      <div style={{ display: 'flex', alignItems: 'flex-start', flex: 1 }}>
        {/* Desktop spine */}
        {!isMobile && (
          <JourneySpine
            stages={course.stages}
            currentStage={state.currentStage}
            unlocked={state.unlocked}
            mastery={state.mastery}
            onSelect={setCurrentStage}
          />
        )}

        {/* Main content */}
        <main style={{ flex: 1, minWidth: 0 }}>
          <StageView
            key={currentStage.id}
            stage={currentStage}
            stageIndex={state.currentStage}
            totalStages={course.stages.length}
            mastery={state.mastery}
            drills={state.drills}
            onMastery={handleMastery}
            onDrill={handleDrill}
            onNext={handleNextStage}
            isLast={state.currentStage === course.stages.length - 1}
          />
        </main>
      </div>
    </div>
  );
}

function MiniProgress({ course, mastery }) {
  const total = course.stages.reduce((s, stg) => s + stg.concepts.length, 0);
  const m = Object.values(mastery || {}).filter(v => v === 'mastered').length;
  const pct = total > 0 ? m / total : 0;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <ProgressRing size={28} stroke={2.5} progress={pct} />
      <span style={{
        fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-3)',
      }}>{m}/{total}</span>
    </div>
  );
}

// ── Mount ────────────────────────────────────────────────────
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(App));
