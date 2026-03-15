import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { COLORS, FPS } from "../lib/theme";
import { fadeIn, fadeOut, slideUp, pulse, glowShadow } from "../lib/animations";

const { fontFamily } = loadFont("normal", {
  weights: ["400", "700"],
  subsets: ["latin"],
});

const DURATION = 300; // 10s at 30fps

// 24 floating particles across the full screen
const PARTICLES = Array.from({ length: 24 }, (_, i) => ({
  x: (i * 137 + 83) % 1920,
  speed: 0.3 + ((i * 0.13) % 0.5),
  size: 4 + (i % 3) * 1,
  color: [COLORS.skyBlue, COLORS.violet, COLORS.coral, COLORS.emerald, COLORS.amber][i % 5],
  opacity: 0.1 + (i % 4) * 0.03,
  wobbleAmp: 15 + (i % 4) * 10,
  wobbleFreq: 0.02 + (i % 5) * 0.004,
  startY: 1080 + (i * 91) % 300,
}));

const IVR_PROMPTS = [
  { text: '"Press 1 for billing..."', inFrame: 60, outFrame: 130 },
  { text: '"Press 2 for support..."', inFrame: 130, outFrame: 200 },
  {
    text: '"Please hold, your call is important to us..."',
    inFrame: 200,
    outFrame: 270,
  },
];

const HeadlineText: React.FC = () => {
  const frame = useCurrentFrame();

  // Instant appearance with a spring punch scale
  const scale = spring({
    frame,
    fps: FPS,
    config: {
      damping: 200,
      mass: 0.6,
      stiffness: 300,
    },
    from: 0.95,
    to: 1,
  });

  // Coral underline grows from 0 to 80px over first 15 frames
  const lineWidth = interpolate(frame, [0, 15], [0, 80], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.exp),
  });

  // Fade out at end
  const exitOpacity = 1; // let TransitionSeries handle fade

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 16,
        opacity: exitOpacity,
        transform: `scale(${scale})`,
      }}
    >
      <div
        style={{
          fontFamily,
          fontSize: 96,
          fontWeight: 700,
          color: COLORS.white,
          textAlign: "center",
          lineHeight: 1.1,
        }}
      >
        47 minutes on hold.
      </div>
      <div
        style={{
          width: lineWidth,
          height: 3,
          background: COLORS.coral,
          borderRadius: 2,
        }}
      />
    </div>
  );
};

const HoldTimer: React.FC = () => {
  const frame = useCurrentFrame();

  // Timer starts at 47:12 and counts up — advance ~0.4s per frame for visible counting
  const baseSeconds = 47 * 60 + 12;
  const elapsed = Math.max(0, frame - 15);
  const currentSeconds = baseSeconds + Math.floor(elapsed * 0.4);
  const minutes = Math.floor(currentSeconds / 60);
  const seconds = currentSeconds % 60;
  const timerStr = `00:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  const timerOpacity = fadeIn(frame, 15, 20);
  const exitOpacity = 1; // let TransitionSeries handle fade

  return (
    <div
      style={{
        fontFamily,
        fontSize: 120,
        fontWeight: 700,
        color: COLORS.coral,
        opacity: Math.min(timerOpacity, exitOpacity),
        fontVariantNumeric: "tabular-nums",
        textShadow: glowShadow(COLORS.coral, 0.4),
        letterSpacing: 3,
        textAlign: "center",
      }}
    >
      {timerStr}
    </div>
  );
};

const IvrPrompts: React.FC = () => {
  const frame = useCurrentFrame();
  const FADE_DUR = 15;
  const exitOpacity = 1; // let TransitionSeries handle fade

  return (
    <div
      style={{
        position: "relative",
        height: 40,
        width: "100%",
        opacity: exitOpacity,
      }}
    >
      {IVR_PROMPTS.map((prompt, i) => {
        const fadeInStart = prompt.inFrame;
        const fadeOutStart = prompt.outFrame - FADE_DUR;
        let opacity = 0;

        if (frame >= fadeInStart && frame < fadeInStart + FADE_DUR) {
          opacity = fadeIn(frame, fadeInStart, FADE_DUR);
        } else if (frame >= fadeInStart + FADE_DUR && frame < fadeOutStart) {
          opacity = 1;
        } else if (frame >= fadeOutStart && frame < prompt.outFrame) {
          opacity = fadeOut(frame, fadeOutStart, FADE_DUR);
        }

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              width: "100%",
              textAlign: "center",
              fontFamily,
              fontSize: 20,
              color: COLORS.gray400,
              fontStyle: "italic",
              opacity,
            }}
          >
            {prompt.text}
          </div>
        );
      })}
    </div>
  );
};

const PhoneOutlines: React.FC = () => {
  const frame = useCurrentFrame();

  const enterOpacity = fadeIn(frame, 120, 30);
  const exitOpacity = 1; // let TransitionSeries handle fade
  const opacity = Math.min(enterOpacity, exitOpacity);

  // Slow drift inward
  const drift = interpolate(frame, [120, 250], [0, 20], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  return (
    <>
      {/* Left phone outline */}
      <div
        style={{
          position: "absolute",
          left: 120 + drift,
          top: "50%",
          transform: "translateY(-50%)",
          width: 200,
          height: 360,
          borderRadius: 40,
          border: `2px solid ${COLORS.gray600}`,
          opacity: opacity * 0.15,
        }}
      />
      {/* Right phone outline */}
      <div
        style={{
          position: "absolute",
          right: 120 + drift,
          top: "50%",
          transform: "translateY(-50%)",
          width: 200,
          height: 360,
          borderRadius: 40,
          border: `2px solid ${COLORS.gray600}`,
          opacity: opacity * 0.15,
        }}
      />
    </>
  );
};

const FloatingParticles: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <>
      {PARTICLES.map((p, i) => {
        const y = p.startY - frame * p.speed * 3;
        const x = p.x + Math.sin(frame * p.wobbleFreq + i) * p.wobbleAmp;
        const particleOpacity = interpolate(
          y,
          [-50, 200, 900, 1080],
          [0, p.opacity, p.opacity, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y % 1200,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              background: p.color,
              opacity: particleOpacity,
              filter: `blur(${p.size > 5 ? 1 : 0}px)`,
            }}
          />
        );
      })}
    </>
  );
};

export const PainScene: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        fontFamily,
        background: `radial-gradient(ellipse at 50% 45%, #1a1a30 0%, #10101e 40%, #08080f 100%)`,
        overflow: "hidden",
      }}
    >
      {/* Grid dot texture */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `radial-gradient(circle, ${COLORS.gray600}1a 1px, transparent 1px)`,
          backgroundSize: "50px 50px",
        }}
      />

      {/* Floating particles */}
      <FloatingParticles />

      {/* Phone outlines — appear at frame 120 */}
      <PhoneOutlines />

      {/* Center content — fills the screen */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 24,
        }}
      >
        <HeadlineText />
        <HoldTimer />
        <IvrPrompts />
      </div>
    </AbsoluteFill>
  );
};

export default PainScene;
