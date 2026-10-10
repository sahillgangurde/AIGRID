import {describe,it,expect} from 'vitest';
import {swipeVelocity,loopPosition} from '@/lib/film-wheel-motion';
describe('Film wheel motion',()=>{
 it('moves faster for a stronger upward swipe',()=>{expect(swipeVelocity(120,100)).toBeGreaterThan(swipeVelocity(30,100));});
 it('preserves downward swipe direction',()=>{expect(swipeVelocity(-120,100)).toBe(-1.2);});
 it('loops in both directions',()=>{expect(loopPosition(99,100)).toBe(199);expect(loopPosition(301,100)).toBe(201);});
});