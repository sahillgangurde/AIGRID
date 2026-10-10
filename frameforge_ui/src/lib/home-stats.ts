export const homeStats = [
 { value: 1053, label: 'Creators' },
 { value: 179, label: 'Content traded' },
 { value: 7, label: 'Briefs generated' },
 { value: 1, label: 'Matchings' },
];
export function countAtProgress(value: number, progress: number) {
 const clamped = Math.max(0, Math.min(1, progress));
 return Math.floor(value * (1 - Math.pow(1 - clamped, 2)));
}