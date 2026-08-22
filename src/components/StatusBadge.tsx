import { APPLICATION_STATUSES, type ApplicationStatus } from '../types'

// A monochrome intensity progression rather than a color per status: quiet/undecided (hairline) ->
// in motion (accent outline, then accent outline+fill) -> the two terminal outcomes get a solid
// fill each, positive in accent, negative in ink (not a new error hue).
const STYLES: Record<ApplicationStatus, string> = {
  not_started: 'border border-hairline bg-surface text-ink-muted',
  waitlisted: 'border border-dashed border-ink-muted bg-surface text-ink-muted',
  applying: 'border border-accent bg-surface text-accent',
  submitted: 'border border-accent bg-accent-soft text-accent',
  accepted: 'border border-accent bg-accent text-paper',
  rejected: 'border border-ink bg-ink text-paper',
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
      className={`cursor-pointer rounded-sm px-2.5 py-1 text-xs font-medium tracking-wide focus:outline-none focus:ring-2 focus:ring-accent ${STYLES[status]}`}
    >
      {APPLICATION_STATUSES.map((s) => (
        <option key={s.value} value={s.value}>
          {s.label}
        </option>
      ))}
    </select>
  )
}
