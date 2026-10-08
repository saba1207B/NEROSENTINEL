'use client';

import { useEffect, useRef } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';

const chapters = [
  { title: 'Start with the evidence.', description: 'Every pilot value carries a source type and a synthetic-data label. No observed district record is implied.', href: '/dashboard/climate', image: '/forest/climate.svg', alt: 'Earth toned climate signal line against forest green rings' },
  { title: 'Follow the water.', description: 'A monthly ledger separates rainfall runoff, storage, evaporation, release and conveyance loss.', href: '/dashboard/twin', image: '/forest/reservoir.svg', alt: 'Layered reservoir landscape in forest and sage tones' },
  { title: 'Test what may change.', description: 'Compare declared rainfall and temperature cases in the bounded digital twin. The result is a scenario, not a forecast.', href: '/dashboard/simulator', image: '/forest/climate.svg', alt: 'Earth toned climate signal line representing scenario comparisons' },
  { title: 'Keep decisions human.', description: 'Intervention plans expose assumptions, costs and limitations. The backend does not operate dams or issue public warnings.', href: '/dashboard/warnings', image: '/forest/field.svg', alt: 'Terraced field contours in the pilot landscape palette' },
];
const themes = ['#fefae0', '#ccd5ae', '#e9edc9', '#a3b18a'];

export function PinnedEvidenceStory() {
  const root = useRef<HTMLElement>(null);
  useEffect(() => {
    const section = root.current;
    if (!section) return;
    const blocks = Array.from(section.querySelectorAll<HTMLElement>('.arch__block'));
    const frames = Array.from(section.querySelectorAll<HTMLElement>('.arch__frame'));
    const right = section.querySelector<HTMLElement>('.arch__right');
    if (!right || blocks.length !== chapters.length || frames.length !== chapters.length) return;
    gsap.registerPlugin(ScrollTrigger);
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const mm = gsap.matchMedia();
    let lenis: Lenis | null = null;
    let tick: ((time: number) => void) | null = null;
    if (!reduced) {
      lenis = new Lenis({ autoRaf: false, duration: 1.05 });
      lenis.on('scroll', ScrollTrigger.update);
      tick = (time: number) => lenis?.raf(time * 1000);
      gsap.ticker.add(tick);
      gsap.ticker.lagSmoothing(0);
    }
    mm.add('(min-width: 769px)', () => {
      if (reduced) return;
      ScrollTrigger.create({ trigger: section, start: 'top top', end: 'bottom bottom', pin: right, pinSpacing: false });
      blocks.forEach((block, index) => {
        ScrollTrigger.create({ trigger: block, start: 'top center', end: 'bottom center', onEnter: () => gsap.to(section, { backgroundColor: themes[index], duration: 0.45 }), onEnterBack: () => gsap.to(section, { backgroundColor: themes[index], duration: 0.45 }) });
        if (index === 0) return;
        gsap.to(frames[index - 1], { clipPath: 'inset(0 0 100% 0)', ease: 'none', scrollTrigger: { trigger: block, start: 'top bottom', end: 'top center', scrub: true } });
        const image = frames[index - 1].querySelector('img');
        if (image) gsap.to(image, { objectPosition: '50% 70%', ease: 'none', scrollTrigger: { trigger: block, start: 'top bottom', end: 'top center', scrub: true } });
      });
    });
    mm.add('(max-width: 768px)', () => {
      blocks.forEach((block, index) => { block.style.order = String(index * 2); frames[index].style.order = String(index * 2 + 1); });
      if (reduced) return () => { blocks.forEach((block) => block.style.removeProperty('order')); frames.forEach((frame) => frame.style.removeProperty('order')); };
      frames.forEach((frame, index) => {
        const image = frame.querySelector('img');
        if (image) gsap.fromTo(image, { objectPosition: '50% 35%' }, { objectPosition: '50% 65%', ease: 'none', scrollTrigger: { trigger: frame, start: 'top bottom', end: 'bottom top', scrub: true } });
        ScrollTrigger.create({ trigger: frame, start: 'top 60%', onEnter: () => gsap.to(section, { backgroundColor: themes[index], duration: 0.4 }), onEnterBack: () => gsap.to(section, { backgroundColor: themes[index], duration: 0.4 }) });
      });
      return () => { blocks.forEach((block) => block.style.removeProperty('order')); frames.forEach((frame) => frame.style.removeProperty('order')); };
    });
    ScrollTrigger.refresh();
    return () => { mm.revert(); if (tick) gsap.ticker.remove(tick); lenis?.destroy(); };
  }, []);

  return <section ref={root} className="arch" aria-labelledby="arch-title"><div className="arch__inner"><div className="arch__left"><div className="arch__intro"><p className="arch__eyebrow">A clearer path through uncertainty</p><h2 id="arch-title">From evidence to reviewable action</h2></div>{chapters.map((chapter, index) => <article key={chapter.title} className="arch__block"><span className="arch__number">0{index + 1} / 04</span><h3>{chapter.title}</h3><p>{chapter.description}</p><Link href={chapter.href} className="arch__button">Learn more <span aria-hidden="true">↗</span></Link></article>)}</div><div className="arch__right">{chapters.map((chapter, index) => <div key={chapter.image} className="arch__frame" style={{ zIndex: chapters.length - index }}><Image src={chapter.image} alt={chapter.alt} fill sizes="(max-width: 768px) 100vw, 540px" priority={index === 0} /></div>)}</div></div></section>;
}
