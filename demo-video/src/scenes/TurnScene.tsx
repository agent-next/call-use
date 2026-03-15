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

const DURATION = 150; // 5s at 30fps

// 25 particle burst from center
const BURST_PARTICLES = Array.from({ length: 25 }, (_, i) => {
  const angle = (i / 25) * Math.PI * 2 + ((i * 0.37) % 1);
  return {
    angle,
    speed: 140 + (i * 41) % 100,
    size: 3 + (i % 3),
    color: [COLORS.skyBlue, COLORS.emerald, COLORS.violet, COLORS.amber, COLORS.coral][i % 5],
  };
});

const QuestionText: React.FC = () => {
  const frame = useCurrentFrame();

  const line1Opacity = fadeIn(frame, 0, 20);
  const line1Y = slideUp(frame, 0, 20, 40);

  const line2Opacity = fadeIn(frame, 15, 20);
  const line2Y = slideUp(frame, 15, 20, 40);

  // Fade out both
  const exitOpacity = fadeOut(frame, 50, 15);

  const combinedOpacity1 = Math.min(line1Opacity, exitOpacity);
  const combinedOpacity2 = Math.min(line2Opacity, exitOpacity);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
      }}
    >
      <div
        style={{
          fontFamily,
          fontSize: 64,
          fontWeight: 400,
          color: `${COLORS.white}e6`,
          opacity: combinedOpacity1,
          transform: `translateY(${line1Y}px)`,
          textAlign: "center",
        }}
      >
        What if your AI
      </div>
      <div
        style={{
          fontFamily,
          fontSize: 64,
          fontWeight: 400,
          color: `${COLORS.white}e6`,
          opacity: combinedOpacity2,
          transform: `translateY(${line2Y}px)`,
          textAlign: "center",
        }}
      >
        could{" "}
        <span
          style={{
            color: COLORS.skyBlue,
            textShadow: glowShadow(COLORS.skyBlue, 0.3),
          }}
        >
          make the call
        </span>{" "}
        for you?
      </div>
    </div>
  );
};

const LogoReveal: React.FC = () => {
  const frame = useCurrentFrame();

  // Spring scale animation starting at frame 60
  const logoScale = spring({
    frame: Math.max(0, frame - 60),
    fps: FPS,
    config: {
      damping: 12,
      mass: 0.8,
      stiffness: 100,
    },
  });

  const logoOpacity = fadeIn(frame, 60, 15);

  // Line width grows from center — frame 80 to 110
  const lineWidth = interpolate(frame, [80, 110], [0, 160], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.exp),
  });

  const subtitleOpacity = fadeIn(frame, 95, 20);
  const subtitleY = slideUp(frame, 95, 20, 15);

  // Ambient glow pulse
  const glowOpacity = 0.06 + 0.04 * Math.sin(frame * 0.06);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 20,
        position: "relative",
      }}
    >
      {/* Large ambient glow behind logo — 800px radius */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: 800,
          height: 800,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${COLORS.skyBlue} 0%, transparent 70%)`,
          opacity: glowOpacity,
          pointerEvents: "none",
        }}
      />

      {/* Logo text — MASSIVE 120px */}
      <div
        style={{
          fontFamily,
          fontSize: 120,
          fontWeight: 700,
          color: COLORS.white,
          opacity: logoOpacity,
          transform: `scale(${logoScale})`,
          whiteSpace: "nowrap",
        }}
      >
        call
        <span style={{ color: COLORS.skyBlue }}>-</span>
        use
      </div>

      {/* Horizontal line — skyBlue */}
      <div
        style={{
          width: lineWidth,
          height: 2,
          background: `${COLORS.skyBlue}80`,
          borderRadius: 1,
        }}
      />

      {/* Subtitle */}
      <div
        style={{
          fontFamily,
          fontSize: 22,
          fontWeight: 400,
          color: COLORS.gray400,
          opacity: subtitleOpacity,
          transform: `translateY(${subtitleY}px)`,
          letterSpacing: 1,
        }}
      >
        open source voice agent runtime
      </div>
    </div>
  );
};

const ParticleBurst: React.FC = () => {
  const frame = useCurrentFrame();

  if (frame < 60) return null;

  const burstFrame = frame - 60;

  return (
    <>
      {BURST_PARTICLES.map((p, i) => {
        const distance = spring({
          frame: burstFrame,
          fps: FPS,
          config: {
            damping: 18,
            mass: 0.5,
            stiffness: 80,
          },
        });

        const travel = distance * p.speed;
        const x = 960 + Math.cos(p.angle) * travel;
        const y = 540 + Math.sin(p.angle) * travel;

        const opacity = interpolate(burstFrame, [0, 10, 50], [0, 0.5, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - p.size / 2,
              top: y - p.size / 2,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              background: p.color,
              opacity,
              filter: "blur(0.5px)",
            }}
          />
        );
      })}
    </>
  );
};

export const TurnScene: React.FC = () => {
  const frame = useCurrentFrame();

  // Background interpolation — stays dark
  const bgProgress = interpolate(frame, [0, 60], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const centerR = Math.round(interpolate(bgProgress, [0, 1], [0x1a, 0x0c]));
  const centerG = Math.round(interpolate(bgProgress, [0, 1], [0x1a, 0x12]));
  const centerB = Math.round(interpolate(bgProgress, [0, 1], [0x30, 0x22]));
  const centerColor = `rgb(${centerR}, ${centerG}, ${centerB})`;

  const edgeR = Math.round(interpolate(bgProgress, [0, 1], [0x08, 0x08]));
  const edgeG = Math.round(interpolate(bgProgress, [0, 1], [0x08, 0x08]));
  const edgeB = Math.round(interpolate(bgProgress, [0, 1], [0x0f, 0x10]));
  const edgeColor = `rgb(${edgeR}, ${edgeG}, ${edgeB})`;

  const showQuestion = frame < 65;
  const showLogo = frame >= 55;

  return (
    <AbsoluteFill
      style={{
        fontFamily,
        background: `radial-gradient(ellipse at 50% 45%, ${centerColor} 0%, ${edgeColor} 100%)`,
        overflow: "hidden",
      }}
    >
      {/* Particle burst */}
      <ParticleBurst />

      {/* Center content */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {showQuestion && <QuestionText />}
        {showLogo && <LogoReveal />}
      </div>
    </AbsoluteFill>
  );
};

export default TurnScene;
