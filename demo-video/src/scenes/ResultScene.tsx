import React from "react";
import { useCurrentFrame, spring, interpolate } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { COLORS, FPS } from "../lib/theme";
import { fadeIn, stagger, glowShadow } from "../lib/animations";

const { fontFamily } = loadFont("normal", {
  weights: ["400", "700"],
  subsets: ["latin"],
});

const MetricTile: React.FC<{
  index: number;
  label: string;
  children: React.ReactNode;
}> = ({ index, label, children }) => {
  const frame = useCurrentFrame();
  const anim = stagger(frame, index, 10, 20);

  return (
    <div
      style={{
        background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.05)",
        borderRadius: 14,
        padding: 24,
        opacity: anim.opacity,
        transform: `translateY(${anim.y}px)`,
        display: "flex",
        flexDirection: "column",
        gap: 10,
      }}
    >
      <span
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: COLORS.gray500,
          letterSpacing: 2,
          textTransform: "uppercase",
          fontFamily,
        }}
      >
        {label}
      </span>
      {children}
    </div>
  );
};

export const ResultScene: React.FC = () => {
  const frame = useCurrentFrame();

  const bgStyle: React.CSSProperties = {
    width: "100%",
    height: "100%",
    background:
      "radial-gradient(ellipse 80% 80% at 50% 50%, #0d1117 0%, #060810 100%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily,
  };

  const cardScale = spring({
    frame,
    fps: FPS,
    from: 0.9,
    to: 1,
    config: { damping: 200 },
  });

  const cardOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div style={bgStyle}>
      <div
        style={{
          width: 900,
          height: 520,
          background: "#141825",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 20,
          boxShadow: "0 40px 80px rgba(0,0,0,0.5)",
          transform: `scale(${cardScale})`,
          opacity: cardOpacity,
          padding: "36px 44px",
          display: "flex",
          flexDirection: "column",
          boxSizing: "border-box",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
          }}
        >
          {/* Success circle */}
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: "50%",
              background: `linear-gradient(135deg, ${COLORS.emerald}, ${COLORS.deepEmerald})`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: glowShadow(COLORS.emerald, 0.6),
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 700,
                color: COLORS.white,
                lineHeight: 1,
                fontFamily,
              }}
            >
              &#10003;
            </span>
          </div>

          {/* Text */}
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span
              style={{
                fontSize: 36,
                fontWeight: 700,
                color: COLORS.white,
                fontFamily,
              }}
            >
              Call Completed
            </span>
            <span
              style={{
                fontSize: 16,
                color: COLORS.gray400,
                fontFamily,
              }}
            >
              Duration: 2m 34s
            </span>
          </div>
        </div>

        {/* Divider */}
        <div
          style={{
            width: "100%",
            height: 1,
            background: "rgba(255,255,255,0.06)",
            marginTop: 24,
          }}
        />

        {/* Metric tiles 2x2 grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 20,
            marginTop: 24,
            flex: 1,
          }}
        >
          {/* Tile 1: Disposition */}
          <MetricTile index={0} label="DISPOSITION">
            <span
              style={{
                display: "inline-block",
                background: `${COLORS.emerald}26`,
                color: COLORS.emerald,
                fontSize: 16,
                fontWeight: 700,
                borderRadius: 8,
                padding: "6px 16px",
                fontFamily,
                alignSelf: "flex-start",
              }}
            >
              completed
            </span>
          </MetricTile>

          {/* Tile 2: Refund */}
          <MetricTile index={1} label="REFUND PROCESSED">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: COLORS.emerald,
                  fontFamily,
                }}
              >
                $49.99
              </span>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: COLORS.emerald,
                  background: `${COLORS.emerald}1a`,
                  borderRadius: 6,
                  padding: "3px 10px",
                  textTransform: "uppercase",
                  letterSpacing: 1,
                  fontFamily,
                }}
              >
                approved
              </span>
            </div>
          </MetricTile>

          {/* Tile 3: Conversation Turns */}
          <MetricTile index={2} label="CONVERSATION TURNS">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: COLORS.white,
                  fontFamily,
                }}
              >
                12
              </span>
              <span style={{ fontSize: 22 }}>&#x1F4AC;</span>
            </div>
          </MetricTile>

          {/* Tile 4: Menu Navigations */}
          <MetricTile index={3} label="MENU NAVIGATIONS">
            <span
              style={{
                fontSize: 32,
                fontWeight: 700,
                color: COLORS.skyBlue,
                fontFamily,
              }}
            >
              3
            </span>
          </MetricTile>
        </div>

        {/* Bottom bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginTop: 12,
            opacity: fadeIn(frame, 80, 20),
          }}
        >
          <span
            style={{
              fontSize: 14,
              color: COLORS.gray400,
              fontFamily,
            }}
          >
            Full transcript and recording available &rarr;
          </span>
        </div>
      </div>
    </div>
  );
};

export default ResultScene;
