import { useEffect, useState } from 'react'

/**
 * Minimal hash-based routing for 3 flat pages — no router dependency needed, and hash fragments
 * never hit the server, so this needs zero GitHub Pages config (unlike a path-based router, which
 * would need a 404.html fallback trick to survive a direct navigation/refresh on a sub-path).
 */
export function useHashRoute(defaultRoute: string): [string, (route: string) => void] {
  const [route, setRoute] = useState(() => window.location.hash.slice(1) || defaultRoute)

  useEffect(() => {
    const onHashChange = () => setRoute(window.location.hash.slice(1) || defaultRoute)
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [defaultRoute])

  const navigate = (next: string) => {
    window.location.hash = next
  }

  return [route, navigate]
}
