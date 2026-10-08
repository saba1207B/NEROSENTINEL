'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';

export function RevealObserver() {
  const pathname = usePathname();

  useEffect(() => {
    const root = document.querySelector<HTMLElement>('.dashboard-shell main, .home-shell main');
    if (!root || window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return;
    const isHome = Boolean(root.closest('.home-shell'));
    const page = root.firstElementChild?.firstElementChild;
    const targets = isHome
      ? Array.from(root.querySelectorAll<HTMLElement>('#platform .feature-card, #method, #limits'))
      : Array.from(page?.children || []).filter((element): element is HTMLElement => element instanceof HTMLElement);
    if (targets.length === 0) return;
    targets.forEach((element) => element.setAttribute('data-reveal', ''));
    root.classList.add('reveal-root', 'reveal-active');

    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.setAttribute('data-visible', 'true');
        observer.unobserve(entry.target);
      }
    }, { threshold: 0.08, rootMargin: '0px 0px -48px 0px' });
    targets.forEach((target) => observer.observe(target));

    return () => {
      observer.disconnect();
      root.classList.remove('reveal-root', 'reveal-active');
      targets.forEach((element) => {
        element.removeAttribute('data-reveal');
        element.removeAttribute('data-visible');
      });
    };
  }, [pathname]);

  return null;
}
