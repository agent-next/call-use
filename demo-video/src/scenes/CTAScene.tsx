import React, { useMemo } from "react";
import {
  useCurrentFrame,
  spring,
  interpolate,
  Sequence,
  AbsoluteFill,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { COLORS, FPS } from "../lib/theme";
import { fadeIn, slideUp, stagger } from "../lib/animations";

const { fontFamily } = loadFont("normal", {
  weights: ["400", "700"],
  subsets: ["latin"],
});

// Deterministic particle generation
const generateParticles = (count: number) => {
  const particles = [];
  for (let i = 0; i < count; i++) {
    const seed = i * 137.508; // golden angle
    particles.push({
      x: (seed * 7.3) % 100,
      startY: 100 + ((seed * 3.1) % 20),
      size: 3 + ((seed * 1.7) % 1),
      speed: 0.3 + ((seed * 0.9) % 0.4),
      wobbleAmp: 10 + ((seed * 2.3) % 15),
      wobbleSpeed: 0.03 + ((seed * 0.5) % 0.04),
      opacity: 0.12 + ((seed * 1.1) % 0.08),
      color: [COLORS.skyBlue, COLORS.emerald, COLORS.violet][i % 3],
      delay: (i * 2) % 40,
    });
  }
  return particles;
};

const Particles: React.FC = () => {
  const frame = useCurrentFrame();
  const particles = useMemo(() => generateParticles(25), []);

  return (
    <AbsoluteFill style={{ overflow: "hidden", pointerEvents: "none" }}>
      {particles.map((p, i) => {
        const progress = Math.max(0, frame - p.delay);
        if (progress <= 0) return null;

        const yPos = p.startY - progress * p.speed;
        const xOffset = Math.sin(progress * p.wobbleSpeed) * p.wobbleAmp;
        const particleOpacity = interpolate(
          progress,
          [0, 15, 200],
          [0, p.opacity, 0],
          { extrapolateRight: "clamp", extrapolateLeft: "clamp" },
        );

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${p.x}%`,
              top: `${yPos}%`,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              background: p.color,
              opacity: particleOpacity,
              transform: `translateX(${xOffset}px)`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

const FEATURE_PILLS = [
  "IVR Navigation",
  "Live Transcript",
  "Human Approval",
  "Open Source",
];

export const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();

  // Background ambient glow pulse
  const glowOpacity = interpolate(
    Math.sin(frame * 0.06),
    [-1, 1],
    [0.03, 0.05],
  );

  return (
    <AbsoluteFill
      style={{
        background: "#0a0a14",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily,
      }}
    >
      {/* Ambient glow */}
      <div
        style={{
          position: "absolute",
          width: 1200,
          height: 1200,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${COLORS.skyBlue} 0%, transparent 70%)`,
          opacity: glowOpacity,
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          pointerEvents: "none",
        }}
      />

      {/* Particles */}
      <Sequence from={40}>
        <Particles />
      </Sequence>

      {/* Content stack */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 0,
          zIndex: 1,
        }}
      >
        <LogoBlock />
        <TaglineBlock />
        <SubTaglineBlock />
        <GitHubBlock />
        <FeaturePills />
      </div>
    </AbsoluteFill>
  );
};

const LogoBlock: React.FC = () => {
  const frame = useCurrentFrame();

  const scale = spring({
    frame,
    fps: FPS,
    from: 0,
    to: 1,
    config: { damping: 12, mass: 0.5 },
  });

  return (
    <div
      style={{
        transform: `scale(${scale})`,
        marginBottom: 24,
      }}
    >
      <span
        style={{
          fontSize: 120,
          fontWeight: 700,
          color: COLORS.white,
          fontFamily,
          textShadow: `0 0 60px ${COLORS.skyBlue}33`,
        }}
      >
        call
      </span>
      <span
        style={{
          fontSize: 120,
          fontWeight: 700,
          color: COLORS.skyBlue,
          fontFamily,
          textShadow: `0 0 60px ${COLORS.skyBlue}33`,
        }}
      >
        -
      </span>
      <span
        style={{
          fontSize: 120,
          fontWeight: 700,
          color: COLORS.white,
          fontFamily,
          textShadow: `0 0 60px ${COLORS.skyBlue}33`,
        }}
      >
        use
      </span>
    </div>
  );
};

const TaglineBlock: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = fadeIn(frame, 20, 20);
  const y = slideUp(frame, 20, 20, 20);

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${y}px)`,
        marginBottom: 16,
      }}
    >
      <span
        style={{
          fontSize: 24,
          fontWeight: 400,
          color: COLORS.gray400,
          fontFamily,
        }}
      >
        Open source voice agent runtime
      </span>
    </div>
  );
};

const SubTaglineBlock: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = fadeIn(frame, 35, 20);
  const y = slideUp(frame, 35, 20, 20);

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${y}px)`,
        marginBottom: 32,
      }}
    >
      <span
        style={{
          fontSize: 28,
          fontWeight: 700,
          color: COLORS.gray200,
          fontFamily,
        }}
      >
        Let your AI agent handle the call.
      </span>
    </div>
  );
};

const GitHubBlock: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = fadeIn(frame, 55, 20);
  const y = slideUp(frame, 55, 20, 20);

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${y}px)`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
        marginBottom: 32,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span style={{ fontSize: 18 }}>&#x2B50;</span>
        <span
          style={{
            fontSize: 18,
            color: COLORS.gray400,
            fontFamily,
          }}
        >
          Star on GitHub
        </span>
      </div>
      <span
        style={{
          fontSize: 16,
          color: `${COLORS.skyBlue}99`,
          fontFamily,
        }}
      >
        github.com/agent-next/call-use
      </span>
    </div>
  );
};

const FeaturePills: React.FC = () => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - 70);

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        alignItems: "center",
      }}
    >
      {FEATURE_PILLS.map((pill, i) => {
        const anim = stagger(localFrame, i, 8, 20);
        return (
          <div
            key={pill}
            style={{
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 24,
              padding: "8px 20px",
              opacity: anim.opacity,
              transform: `translateY(${anim.y}px)`,
            }}
          >
            <span
              style={{
                fontSize: 15,
                color: COLORS.gray400,
                fontFamily,
              }}
            >
              {pill}
            </span>
          </div>
        );
      })}
    </div>
  );
};

export default CTAScene;
