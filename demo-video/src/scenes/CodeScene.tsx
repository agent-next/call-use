import React from "react";
import { useCurrentFrame, interpolate, spring } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { COLORS } from "../lib/theme";
import { fadeIn, slideUp } from "../lib/animations";

const { fontFamily } = loadFont("normal", {
  weights: ["400", "700"],
  subsets: ["latin"],
});
const { fontFamily: monoFamily } = loadMono("normal", {
  weights: ["400"],
  subsets: ["latin"],
});

/* ── main component ── */

export const CodeScene: React.FC = () => {
  const frame = useCurrentFrame();

  // Chat window entrance spring
  const windowScale = spring({
    frame,
    fps: 30,
    config: { damping: 200, stiffness: 120, mass: 0.8 },
    from: 0.92,
    to: 1,
    durationInFrames: 20,
  });

  // Message animations
  const msg1Opacity = fadeIn(frame, 40, 20);
  const msg1Y = slideUp(frame, 40, 20, 30);

  const msg2Opacity = fadeIn(frame, 100, 20);
  const msg2Y = slideUp(frame, 100, 20, 30);

  const msg3Opacity = fadeIn(frame, 170, 20);
  const msg3Y = slideUp(frame, 170, 20, 30);

  const msg4Opacity = fadeIn(frame, 270, 20);
  const msg4Y = slideUp(frame, 270, 20, 30);

  // Typing indicator (frame 370+)
  const typingOpacity = fadeIn(frame, 370, 20);
  const typingY = slideUp(frame, 370, 20, 20);

  // Animated dots for action card (frame 170+)
  const dotCount = frame >= 170 ? (Math.floor((frame - 170) / 15) % 3) + 1 : 0;
  const dotsText = ".".repeat(dotCount);

  // Bouncing dots for typing indicator
  const dot1Y = Math.sin((frame - 370) * 0.2) * 5;
  const dot2Y = Math.sin((frame - 370) * 0.2 + 2.09) * 5;
  const dot3Y = Math.sin((frame - 370) * 0.2 + 4.19) * 5;

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        fontFamily,
        background: `radial-gradient(ellipse at center, #0d1117 0%, #060810 100%)`,
      }}
    >
      {/* ── Chat window ── */}
      <div
        style={{
          width: 1100,
          height: 650,
          transform: `scale(${windowScale})`,
          borderRadius: 20,
          overflow: "hidden",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow:
            "0 40px 100px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.03)",
          background: "#141825",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* ── Chat header bar ── */}
        <div
          style={{
            height: 60,
            background: "#1a2030",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            display: "flex",
            alignItems: "center",
            paddingLeft: 24,
            paddingRight: 24,
            flexShrink: 0,
            borderTopLeftRadius: 20,
            borderTopRightRadius: 20,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: COLORS.emerald,
              }}
            />
            <span
              style={{
                fontSize: 17,
                fontWeight: 700,
                color: COLORS.white,
              }}
            >
              AI Assistant
            </span>
            <span
              style={{
                fontSize: 14,
                color: COLORS.gray400,
              }}
            >
              · Online
            </span>
          </div>
        </div>

        {/* ── Messages area ── */}
        <div
          style={{
            flex: 1,
            padding: "28px 32px",
            display: "flex",
            flexDirection: "column",
            gap: 20,
            overflowY: "hidden",
          }}
        >
          {/* Message 1: USER (right-aligned) */}
          {frame >= 40 && (
            <div
              style={{
                opacity: msg1Opacity,
                transform: `translateY(${msg1Y}px)`,
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-end",
              }}
            >
              <span
                style={{
                  fontSize: 12,
                  color: COLORS.gray500,
                  marginBottom: 6,
                }}
              >
                You
              </span>
              <div
                style={{
                  maxWidth: "55%",
                  background: "#2563eb",
                  borderRadius: "20px 20px 6px 20px",
                  padding: "16px 20px",
                }}
              >
                <span
                  style={{
                    fontSize: 17,
                    color: COLORS.white,
                    lineHeight: 1.5,
                  }}
                >
                  Cancel my AT&T subscription and get a refund for this month
                </span>
              </div>
            </div>
          )}

          {/* Message 2: AGENT (left-aligned) */}
          {frame >= 100 && (
            <div
              style={{
                opacity: msg2Opacity,
                transform: `translateY(${msg2Y}px)`,
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  marginBottom: 6,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: COLORS.skyBlue,
                  }}
                />
                <span style={{ fontSize: 12, color: COLORS.gray400 }}>
                  AI Agent
                </span>
              </div>
              <div
                style={{
                  maxWidth: "55%",
                  background: "rgba(255,255,255,0.07)",
                  borderRadius: "20px 20px 20px 6px",
                  padding: "16px 20px",
                }}
              >
                <span
                  style={{
                    fontSize: 17,
                    color: COLORS.gray200,
                    lineHeight: 1.5,
                  }}
                >
                  I'll handle that. Let me call AT&T customer service right now.
                </span>
              </div>
            </div>
          )}

          {/* Message 3: ACTION CARD (left-aligned) */}
          {frame >= 170 && (
            <div
              style={{
                opacity: msg3Opacity,
                transform: `translateY(${msg3Y}px)`,
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
              }}
            >
              <div
                style={{
                  width: 400,
                  background: "rgba(56,189,248,0.06)",
                  border: "1px solid rgba(56,189,248,0.15)",
                  borderRadius: 16,
                  padding: 20,
                }}
              >
                <div
                  style={{
                    fontSize: 16,
                    fontWeight: 700,
                    color: COLORS.skyBlue,
                    marginBottom: 8,
                  }}
                >
                  {"📞 Initiating outbound call"}
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    gap: 4,
                  }}
                >
                  <span
                    style={{
                      fontSize: 22,
                      fontFamily: monoFamily,
                      color: COLORS.white,
                    }}
                  >
                    +1 (800) 288-2020
                  </span>
                  <span
                    style={{
                      fontSize: 22,
                      color: COLORS.skyBlue,
                      fontFamily: monoFamily,
                    }}
                  >
                    {dotsText}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 14,
                    color: COLORS.gray400,
                    marginTop: 6,
                  }}
                >
                  AT&T Customer Service
                </div>
              </div>
            </div>
          )}

          {/* Message 4: STATUS CARD (left-aligned, emerald theme) */}
          {frame >= 270 && (
            <div
              style={{
                opacity: msg4Opacity,
                transform: `translateY(${msg4Y}px)`,
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
              }}
            >
              <div
                style={{
                  width: 400,
                  background: "rgba(52,211,153,0.06)",
                  border: "1px solid rgba(52,211,153,0.15)",
                  borderRadius: 16,
                  padding: 20,
                }}
              >
                <div
                  style={{
                    fontSize: 16,
                    fontWeight: 700,
                    color: COLORS.emerald,
                    marginBottom: 6,
                  }}
                >
                  ✓ Connected to representative
                </div>
                <div
                  style={{
                    fontSize: 14,
                    color: COLORS.gray400,
                  }}
                >
                  Navigated: Press 3 → Cancel Account → Confirm
                </div>
              </div>
            </div>
          )}

          {/* Typing indicator (frame 370+) */}
          {frame >= 370 && (
            <div
              style={{
                opacity: typingOpacity,
                transform: `translateY(${typingY}px)`,
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  background: "rgba(255,255,255,0.06)",
                  borderRadius: 14,
                  padding: "12px 16px",
                }}
              >
                {[dot1Y, dot2Y, dot3Y].map((dy, i) => (
                  <div
                    key={i}
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: COLORS.gray400,
                      transform: `translateY(${dy}px)`,
                    }}
                  />
                ))}
              </div>
              <span style={{ fontSize: 14, color: COLORS.gray500 }}>
                Agent is on the call...
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CodeScene;
