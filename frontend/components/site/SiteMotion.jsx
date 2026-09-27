'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';

const SPOTLIGHT = '.card--link, .step, .metric';
const MAX_TILT = 5; // degrees

// Progressive enhancements that CSS cannot do alone. Renders nothing; every effect is optional,
// so the site looks and works the same without JavaScript.
// - header gains a solid background once the page scrolls
// - cards follow the cursor with a soft spotlight; product frames tilt toward it
// - benchmark numbers count up when they scroll into view
export default function SiteMotion() {
  const pathname = usePathname();

  // Header state and pointer effects: delegated listeners, set up once
  useEffect(() => {
    const header = document.querySelector('.site-header');
    const onScroll = () => header?.toggleAttribute('data-scrolled', window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    if (!finePointer) return () => window.removeEventListener('scroll', onScroll);

    let frame = null;
    let tilted = null;
    let pending = null;

    const resetTilt = () => {
      if (!tilted) return;
      tilted.removeAttribute('data-tilting');
      tilted.style.removeProperty('--rx');
      tilted.style.removeProperty('--ry');
      tilted = null;
    };

    const apply = () => {
      frame = null;
      const { target, x, y } = pending;
      const card = target.closest?.(SPOTLIGHT);
      if (card) {
        const r = card.getBoundingClientRect();
        card.style.setProperty('--mx', `${x - r.left}px`);
        card.style.setProperty('--my', `${y - r.top}px`);
      }
      const tilt = reduce ? null : target.closest?.('[data-tilt]');
      if (tilt !== tilted) resetTilt();
      if (tilt) {
        const r = tilt.getBoundingClientRect();
        const px = (x - r.left) / r.width - 0.5;
        const py = (y - r.top) / r.height - 0.5;
        tilt.style.setProperty('--ry', `${(px * MAX_TILT * 2).toFixed(2)}deg`);
        tilt.style.setProperty('--rx', `${(-py * MAX_TILT * 1.6).toFixed(2)}deg`);
        tilt.setAttribute('data-tilting', '');
        tilted = tilt;
      }
    };

    const onMove = (event) => {
      pending = { target: event.target, x: event.clientX, y: event.clientY };
      if (!frame) frame = requestAnimationFrame(apply);
    };

    document.addEventListener('pointermove', onMove, { passive: true });
    document.documentElement.addEventListener('pointerleave', resetTilt);
    return () => {
      window.removeEventListener('scroll', onScroll);
      document.removeEventListener('pointermove', onMove);
      document.documentElement.removeEventListener('pointerleave', resetTilt);
      if (frame) cancelAnimationFrame(frame);
      resetTilt();
    };
  }, []);

  // Count-up for benchmark figures below the fold. The real value stays in the DOM for
  // screen readers; only an aria-hidden copy animates.
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return;
    // Prepared once per element; effects can re-run (route changes, React strict mode)
    const values = [...document.querySelectorAll('.metric__value')].filter(
      (el) => (el.countUp ? !el.countUp.done : el.getBoundingClientRect().top > window.innerHeight),
    );
    if (!values.length) return;

    const timers = [];
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          observer.unobserve(entry.target);
          entry.target.countUp.done = true;
          const { display, target, suffix } = entry.target.countUp;
          const start = performance.now();
          const duration = 1200;
          const tick = (now) => {
            const t = Math.min(1, (now - start) / duration);
            const eased = 1 - (1 - t) ** 3;
            display.textContent = `${Math.round(target * eased)}${suffix}`;
            if (t < 1) timers.push(requestAnimationFrame(tick));
          };
          timers.push(requestAnimationFrame(tick));
        });
      },
      { threshold: 0.6 },
    );

    values.forEach((el) => {
      if (el.countUp) {
        observer.observe(el);
        return;
      }
      const text = el.textContent.trim();
      const match = text.match(/^(\d+)(.*)$/);
      if (!match) return;
      const display = document.createElement('span');
      display.setAttribute('aria-hidden', 'true');
      display.textContent = `0${match[2]}`;
      const real = document.createElement('span');
      real.className = 'visually-hidden';
      real.textContent = text;
      el.replaceChildren(display, real);
      el.countUp = { display, target: Number(match[1]), suffix: match[2], done: false };
      observer.observe(el);
    });

    return () => {
      observer.disconnect();
      timers.forEach(cancelAnimationFrame);
    };
  }, [pathname]);

  return null;
}
