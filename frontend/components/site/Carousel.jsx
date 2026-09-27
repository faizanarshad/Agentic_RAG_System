'use client';

import { Children, useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { ChevronLeft, ChevronRight, Pause, Play } from 'lucide-react';

const REDUCED = '(prefers-reduced-motion: reduce)';
const subscribeReduced = (onChange) => {
  const query = window.matchMedia(REDUCED);
  query.addEventListener('change', onChange);
  return () => query.removeEventListener('change', onChange);
};
// Server render assumes reduced motion, so nothing autoplays until the browser says otherwise
const useReducedMotion = () => useSyncExternalStore(subscribeReduced, () => window.matchMedia(REDUCED).matches, () => true);

/**
 * Accessible carousel without a library.
 *  variant="fade":  slides are stacked and crossfade (hero showcase).
 *  variant="track": a native scroll-snap row that can be swiped, with pages of however many cards fit.
 * Autoplay (when `interval` is set) advances when the progress bar finishes, so pausing is exact.
 * It pauses on hover, on keyboard focus, off-screen, in background tabs and via the pause button (WCAG 2.2.2),
 * and never runs for visitors who prefer reduced motion.
 */
export default function Carousel({ label, children, variant = 'track', interval = 0, tabs, className = '', tone = 'light' }) {
  const slides = Children.toArray(children);
  const count = slides.length;
  const rootRef = useRef(null);
  const trackRef = useRef(null);
  const [index, setIndex] = useState(0);
  const [pages, setPages] = useState(count);
  const [userPaused, setUserPaused] = useState(false);
  const [held, setHeld] = useState(false);
  const [onScreen, setOnScreen] = useState(false);
  const [tabVisible, setTabVisible] = useState(true);
  const reduced = useReducedMotion();

  const autoplay = interval > 0 && !reduced && count > 1;
  const running = autoplay && !userPaused && !held && onScreen && tabVisible;

  // Track geometry: how many snap positions ("pages") exist for the current width
  const measure = useCallback(() => {
    const track = trackRef.current;
    if (!track || !track.children.length) return null;
    const first = track.children[0];
    const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
    const step = first.getBoundingClientRect().width + gap;
    const perView = Math.max(1, Math.floor((track.clientWidth + gap + 1) / step));
    return { step, pages: Math.max(1, count - perView + 1) };
  }, [count]);

  useEffect(() => {
    if (variant !== 'track' || !trackRef.current) return undefined;
    const observer = new ResizeObserver(() => {
      const m = measure();
      if (m) setPages(m.pages);
    });
    observer.observe(trackRef.current);
    return () => observer.disconnect();
  }, [variant, measure]);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return undefined;
    const io = new IntersectionObserver(([entry]) => setOnScreen(entry.isIntersecting), { threshold: 0.35 });
    io.observe(root);
    const onVisibility = () => setTabVisible(document.visibilityState === 'visible');
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      io.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, []);

  const goTo = useCallback(
    (target) => {
      const total = variant === 'track' ? pages : count;
      const next = ((target % total) + total) % total;
      setIndex(next);
      if (variant === 'track') {
        const m = measure();
        trackRef.current?.scrollTo({ left: m ? next * m.step : 0, behavior: reduced ? 'auto' : 'smooth' });
      }
    },
    [variant, pages, count, measure, reduced],
  );

  // Keep the dots in sync when the visitor swipes or scrolls the track themselves
  const onTrackScroll = () => {
    const m = measure();
    if (!m) return;
    const current = Math.min(m.pages - 1, Math.round(trackRef.current.scrollLeft / m.step));
    if (current !== index) setIndex(current);
  };

  const onKeyDown = (event) => {
    if (event.key === 'ArrowRight') { event.preventDefault(); goTo(index + 1); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); goTo(index - 1); }
  };

  const onBlur = (event) => {
    if (!event.currentTarget.contains(event.relatedTarget)) setHeld(false);
  };

  const total = variant === 'track' ? pages : count;
  const dots = Array.from({ length: total }, (_, i) => i);

  return (
    <section
      ref={rootRef}
      className={`carousel carousel--${variant} carousel--${tone} ${className}`}
      aria-roledescription="carousel"
      aria-label={label}
      onKeyDown={onKeyDown}
      onPointerEnter={(e) => e.pointerType === 'mouse' && setHeld(true)}
      onPointerLeave={() => setHeld(false)}
      onFocus={() => setHeld(true)}
      onBlur={onBlur}
    >
      <div
        ref={trackRef}
        className={variant === 'track' ? 'carousel__track' : 'carousel__stage'}
        aria-live={running ? 'off' : 'polite'}
        onScroll={variant === 'track' ? onTrackScroll : undefined}
        // The scrolling track is keyboard-reachable; arrow keys then move between slides
        tabIndex={variant === 'track' ? 0 : undefined}
      >
        {slides.map((slide, i) => {
          const active = variant === 'fade' ? i === index : true;
          return (
            <div
              key={slide.key ?? i}
              className={`carousel__slide${i === index ? ' is-active' : ''}`}
              role="group"
              aria-roledescription="slide"
              aria-label={tabs ? `${tabs[i]} (${i + 1} of ${count})` : `${i + 1} of ${count}`}
              aria-hidden={active ? undefined : true}
              inert={!active}
            >
              {slide}
            </div>
          );
        })}
      </div>

      {total > 1 && (
        <div className="carousel__controls">
          {tabs ? (
            <div className="carousel__tabs">
              {tabs.map((name, i) => (
                <button key={name} type="button" className="carousel__tab" aria-current={i === index ? 'true' : undefined}
                  aria-label={`Show ${name}`} onClick={() => goTo(i)}>
                  {name}
                </button>
              ))}
            </div>
          ) : (
            <div className="carousel__dots">
              {dots.map((i) => (
                <button key={i} type="button" className="carousel__dot" aria-current={i === index ? 'true' : undefined}
                  aria-label={`Go to slide ${i + 1} of ${total}`} onClick={() => goTo(i)} />
              ))}
            </div>
          )}

          <div className="carousel__buttons">
            {autoplay && (
              <button type="button" className="carousel__btn" onClick={() => setUserPaused(!userPaused)}
                aria-label={userPaused ? 'Start automatic slide show' : 'Pause automatic slide show'}>
                {userPaused ? <Play size={16} aria-hidden="true" /> : <Pause size={16} aria-hidden="true" />}
              </button>
            )}
            <button type="button" className="carousel__btn" onClick={() => goTo(index - 1)} aria-label="Previous slide">
              <ChevronLeft size={18} aria-hidden="true" />
            </button>
            <button type="button" className="carousel__btn" onClick={() => goTo(index + 1)} aria-label="Next slide">
              <ChevronRight size={18} aria-hidden="true" />
            </button>
          </div>

          {autoplay && (
            <span className="carousel__progress" aria-hidden="true">
              <span
                key={`${index}-${userPaused}`}
                style={{ animationDuration: `${interval}ms`, animationPlayState: running ? 'running' : 'paused' }}
                onAnimationEnd={() => goTo(index + 1)}
              />
            </span>
          )}
        </div>
      )}
    </section>
  );
}
