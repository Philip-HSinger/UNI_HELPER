import { AppProvider, useAppContext } from './context/AppContext'
import { useHashRoute } from './hooks/useHashRoute'
import { NavBar } from './components/NavBar'
import { OverviewPage } from './pages/OverviewPage'
import { LikelihoodPage } from './pages/LikelihoodPage'
import { DifficultyPage } from './pages/DifficultyPage'
import { CARD_CLASS_FLUSH } from './lib/uiStyles'

function Shell() {
  const [route, navigate] = useHashRoute('overview')
  const { referenceLoading, referenceError } = useAppContext()

  return (
    <div className="min-h-screen bg-paper pb-16">
      <header className="border-b border-hairline bg-surface">
        <div className="mx-auto max-w-6xl border-b border-hairline px-4 py-6">
          <h1 className="font-display text-3xl font-semibold tracking-tight text-ink">
            Application Efficiency Guide
          </h1>
          <p className="mt-1 font-display text-sm italic text-ink-muted">
            Enter your scores, see where you stand at each school, and find out which supplements
            give you the best score for the writing effort they demand.
          </p>
        </div>
        <NavBar route={route} onNavigate={navigate} />
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        {referenceError ? (
          <div className="rounded-md border border-error p-4 text-sm text-error">
            Couldn't load the school database: {referenceError}
          </div>
        ) : referenceLoading ? (
          <div className={`${CARD_CLASS_FLUSH} p-10 text-center text-sm text-ink-muted`}>Loading schools…</div>
        ) : route === 'likelihood' ? (
          <LikelihoodPage />
        ) : route === 'difficulty' ? (
          <DifficultyPage />
        ) : (
          <OverviewPage />
        )}

        <p className="text-center text-xs text-ink-muted">
          Your own list (scores, which schools you're applying to, status) stays in this browser only — the
          school database and prompt-similarity scores are shared and read from Supabase.
        </p>
      </main>
    </div>
  )
}

function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  )
}

export default App
