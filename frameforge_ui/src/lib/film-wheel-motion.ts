export const FILM_STEP = 388;
export function swipeVelocity(distance: number, elapsedMs: number) {
 return Math.max(-3, Math.min(3, distance / Math.max(1, elapsedMs)));
}
export function loopPosition(position: number, cycle: number) {
 if (position < cycle) return position + cycle;
 if (position >= cycle * 3) return position - cycle;
 return position;
}