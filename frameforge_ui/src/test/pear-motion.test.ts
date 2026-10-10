import { describe, expect, it } from 'vitest';
import { pearPose, pearProgress } from '@/lib/pear-motion';
describe('Scroll-driven pear joining', () => {
  it('starts separated and angled, then joins completely into one pear', () => {
    expect(pearPose(0)).toMatchObject({ separation: 105, leftAngle: -14, rightAngle: 32, rightTurn: -55, turn: 0, leftOpacity: 1 });
    expect(pearPose(1)).toMatchObject({ separation: 0, leftAngle: 0, rightAngle: 0, turn: 180, leftOpacity: 0 });
  });
  it('moves closer and changes angle while scrolling', () => {
    const start = pearPose(.2), later = pearPose(.7);
    expect(later.separation).toBeLessThan(start.separation);
    expect(Math.abs(later.leftAngle)).toBeLessThan(Math.abs(start.leftAngle));
    expect(later.turn).toBeGreaterThan(start.turn);
  });
  it('keeps scroll progress within the separated and connected states', () => {
    expect(pearProgress(900, 1000)).toBe(0);
    expect(pearProgress(600, 1000)).toBe(.5);
    expect(pearProgress(300, 1000)).toBe(1);
  });
  it('visibly rotates the right pear inward and returns it upright when joined', () => {
    expect(pearPose(.5).rightAngle).toBe(16);
    expect(pearPose(.5).rightTurn).toBe(-27.5);
    expect(Math.abs(pearPose(.8).rightAngle)).toBeLessThan(pearPose(.2).rightAngle);
    expect(Math.abs(pearPose(1).rightTurn)).toBe(0);
  });
});