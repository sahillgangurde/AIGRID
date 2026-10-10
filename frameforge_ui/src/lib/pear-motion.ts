export function pearProgress(top: number, viewportHeight: number) {
  return Math.max(0, Math.min(1, (viewportHeight * .85 - top) / (viewportHeight * .5)));
}

export function pearPose(progress: number) {
  const p = Math.max(0, Math.min(1, progress));
  const eased = p * p * (3 - 2 * p);
  return {
    separation: (1 - eased) * 105,
    leftAngle: eased === 1 ? 0 : -14 * (1 - eased),
    rightAngle: 32 * (1 - eased),
    rightTurn: -55 * (1 - eased),
    turn: eased * 180,
    leftOpacity: Math.max(0, 1 - Math.max(0, (p - .85) / .15)),
  };
}