import { describe, expect, it } from 'vitest';
import { creators, homeCreators } from '@/lib/hypear-data';

describe('home page creator section', () => {
  it('shows only the three approved creators, in the agreed order with anonymous aliases', () => {
    expect(homeCreators.map(c => c.slug)).toEqual(['creator-1042', 'creator-1087', 'creator-1126']);
    expect(homeCreators.map(c => c.name)).toEqual(['Creator #1042', 'Creator #1087', 'Creator #1126']);
  });

  it('keeps the other six creators in the directory', () => {
    expect(creators.length).toBe(9);
    expect(homeCreators.every(c => creators.includes(c))).toBe(true);
    expect(creators.filter(c => !homeCreators.includes(c))).toHaveLength(6);
  });
});
