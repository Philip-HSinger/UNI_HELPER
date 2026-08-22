const LINKS: { route: string; label: string }[] = [
  { route: 'overview', label: 'Overview' },
  { route: 'likelihood', label: 'Likelihood of getting in' },
  { route: 'difficulty', label: 'Difficulty of applying' },
]

export function NavBar({ route, onNavigate }: { route: string; onNavigate: (route: string) => void }) {
  return (
    <nav className="flex gap-1 border-b border-hairline px-4">
      {LINKS.map((link) => {
        const active = route === link.route
        return (
          <button
            key={link.route}
            type="button"
            onClick={() => onNavigate(link.route)}
            className={`border-b-2 px-3 py-3 text-sm font-medium tracking-wide transition-colors [font-variant:small-caps] ${
              active ? 'border-accent text-accent' : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            {link.label}
          </button>
        )
      })}
    </nav>
  )
}
