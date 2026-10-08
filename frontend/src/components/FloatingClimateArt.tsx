'use client';

import Image from 'next/image';
import { useEffect, useRef } from 'react';

export function FloatingClimateArt() {
  const art = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = art.current;
    if (!element || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let frame = 0;
    const update = () => {
      if (frame) return;
      frame = window.requestAnimationFrame(() => {
        const offset = Math.max(-42, Math.min(42, window.scrollY * 0.05));
        element.style.setProperty('--parallax-shift', `${offset}px`);
        frame = 0;
      });
    };
    window.addEventListener('scroll', update, { passive: true });
    update();
    return () => { window.removeEventListener('scroll', update); if (frame) window.cancelAnimationFrame(frame); };
  }, []);

  return <div ref={art} className="home-hero__art" aria-label="Illustrated climate and water patterns">
    <div className="floating-art floating-art--main"><Image src="/forest/reservoir.svg" alt="Layered reservoir landscape in forest and sage tones" fill priority sizes="(max-width: 680px) 88vw, 42vw" /></div>
    <div className="floating-art floating-art--top"><Image src="/forest/climate.svg" alt="Abstract climate signal rings" fill sizes="(max-width: 680px) 30vw, 14vw" /></div>
    <div className="floating-art floating-art--small"><Image src="/forest/field.svg" alt="Terraced field contour illustration" fill sizes="(max-width: 680px) 38vw, 20vw" /></div>
    <span className="home-hero__origin">Coimbatore · synthetic pilot</span>
  </div>;
}
