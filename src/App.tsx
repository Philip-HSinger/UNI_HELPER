import { AppProvider, useAppContext } from './context/AppContext'
import { useHashRoute } from './hooks/useHashRoute'
import { NavBar } from './components/NavBar'
import { OverviewPage } from './pages/OverviewPage'
import { LikelihoodPage } from './pages/LikelihoodPage'
import { DifficultyPage } from './pages/DifficultyPage'

function Shell() {
  const [route, navigate] = useHashRoute('overview')
  const { referenceLoading, referenceError } = useAppContext()

  return (
    <div className="min-h-screen bg-slate-50 pb-16 dark:bg-slate-950">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto max-w-6xl px-4 py-6">
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Application Efficiency Guide</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Enter your scores, see where you stand at each school, and find out which supplements
            give you the best score for the writing effort they demand.
          </p>
        </div>
        <NavBar route={route} onNavigate={navigate} />
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        {referenceError ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-300">
            Couldn't load the school database: {referenceError}
          </div>
        ) : referenceLoading ? (
          <div className="rounded-xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-400 dark:border-slate-700 dark:bg-slate-900">
            Loading schools…
          </div>
        ) : route === 'likelihood' ? (
          <LikelihoodPage />
        ) : route === 'difficulty' ? (
          <DifficultyPage />
        ) : (
          <OverviewPage />
        )}

        <p className="text-center text-xs text-slate-400">
          Your own list (scores, committed schools, status) stays in this browser only — the
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
