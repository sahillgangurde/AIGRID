import { describe, expect, it } from 'vitest';
import { creators, homeCreators } from '@/lib/hypear-data';

describe('home page creator section', () => {
  it('shows only the three approved creators, in the agreed order', () => {
    expect(homeCreators.map(c => c.slug)).toEqual(['ananya-rao', 'riddhi-shah', 'kavya-iyer']);
    expect(homeCreators.map(c => c.name)).toEqual(['Ananya Rao', 'Riddhi Shah', 'Kavya Iyer']);
  });

  it('keeps the other six creators in the directory', () => {
    expect(creators.length).toBe(9);
    expect(homeCreators.every(c => creators.includes(c))).toBe(true);
    expect(creators.filter(c => !homeCreators.includes(c))).toHaveLength(6);
  });
});
