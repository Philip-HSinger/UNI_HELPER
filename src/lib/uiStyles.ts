// Shared badge color maps, reused across the Overview/Likelihood/Difficulty pages.
export const CLASSIFICATION_STYLES: Record<string, string> = {
  Reach: 'bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300',
  Match: 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300',
  Safety: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300',
}

export const RECOMMENDATION_STYLES: Record<string, string> = {
  Submit: 'text-emerald-600 dark:text-emerald-400',
  Helps: 'text-emerald-600 dark:text-emerald-400',
  "Don't Submit": 'text-rose-600 dark:text-rose-400',
  Hurts: 'text-rose-600 dark:text-rose-400',
}
