const LINKS: { route: string; label: string }[] = [
  { route: 'overview', label: 'Overview' },
  { route: 'likelihood', label: 'Likelihood of getting in' },
  { route: 'difficulty', label: 'Difficulty of applying' },
]

export function NavBar({ route, onNavigate }: { route: string; onNavigate: (route: string) => void }) {
  return (
    <nav className="flex gap-1 border-b border-slate-200 px-4 dark:border-slate-800">
      {LINKS.map((link) => {
        const active = route === link.route
        return (
          <button
            key={link.route}
            type="button"
            onClick={() => onNavigate(link.route)}
            className={`border-b-2 px-3 py-3 text-sm font-medium transition-colors ${
              active
                ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
          >
            {link.label}
          </button>
        )
      })}
    </nav>
  )
}
