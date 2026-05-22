// Parse an ISO 8601 string into a Date. The backend emits UTC timestamps with
// an explicit offset (e.g. "2026-05-23T13:38:42.160821+00:00"). Only append "Z"
// when no timezone designator is present, otherwise the date becomes invalid.
export function parseISO(iso: string): Date {
  const hasTz = /([zZ])$|[+-]\d{2}:?\d{2}$/.test(iso);
  return new Date(hasTz ? iso : iso + "Z");
}
