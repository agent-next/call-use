import { interpolate, Easing } from "remotion";

export const fadeIn = (
  frame: number,
  start: number,
  dur: number,
): number =>
  interpolate(frame, [start, start + dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

export const fadeOut = (
  frame: number,
  start: number,
  dur: number,
): number =>
  interpolate(frame, [start, start + dur], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.in(Easing.quad),
  });

export const slideUp = (
  frame: number,
  start: number,
  dur: number,
  dist: number = 60,
): number =>
  interpolate(frame, [start, start + dur], [dist, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.exp),
  });

export const typewriterCount = (
  frame: number,
  totalChars: number,
  dur: number,
): number =>
  Math.floor(
    interpolate(frame, [0, dur], [0, totalChars], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );

export const cursorBlink = (frame: number, rate: number = 15): boolean =>
  Math.floor(frame / rate) % 2 === 0;

export const stagger = (
  frame: number,
  index: number,
  delay: number = 10,
  dur: number = 20,
): { opacity: number; y: number } => ({
  opacity: fadeIn(frame, index * delay, dur),
  y: slideUp(frame, index * delay, dur, 30),
});

export const pulse = (frame: number, speed: number = 0.08): number =>
  0.5 + 0.5 * Math.sin(frame * speed);

/** Glow box-shadow string */
export const glowShadow = (color: string, intensity: number): string =>
  `0 0 ${20 * intensity}px ${color}40, 0 0 ${60 * intensity}px ${color}20, 0 0 ${100 * intensity}px ${color}10`;
