import { APPLICATION_STATUSES, type ApplicationStatus } from '../types'

const STYLES: Record<ApplicationStatus, string> = {
  not_started: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
  applying: 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300',
  submitted: 'bg-violet-100 text-violet-700 dark:bg-violet-900/50 dark:text-violet-300',
  accepted: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300',
  rejected: 'bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300',
  waitlisted: 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300',
}

export function StatusBadge({
  status,
  onChange,
}: {
  status: ApplicationStatus
  onChange: (status: ApplicationStatus) => void
}) {
  return (
    <select
      value={status}
      onChange={(e) => onChange(e.target.value as ApplicationStatus)}
      className={`cursor-pointer rounded-full border-0 px-2.5 py-1 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-400 ${STYLES[status]}`}
    >
      {APPLICATION_STATUSES.map((s) => (
        <option key={s.value} value={s.value}>
          {s.label}
        </option>
      ))}
    </select>
  )
}
