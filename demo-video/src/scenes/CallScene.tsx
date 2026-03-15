import React from "react";
import { useCurrentFrame, interpolate, spring, Sequence } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { COLORS } from "../lib/theme";
import {
  fadeIn,
  slideUp,
  typewriterCount,
  pulse,
  glowShadow,
  stagger,
} from "../lib/animations";

const { fontFamily } = loadFont("normal", {
  weights: ["400", "700"],
  subsets: ["latin"],
});
const { fontFamily: monoFamily } = loadMono("normal", {
  weights: ["400"],
  subsets: ["latin"],
});

/* ── sub-components ── */

/** Expanding ring for dialing animation */
const DialRing: React.FC<{ frame: number; delay: number }> = ({
  frame,
  delay,
}) => {
  const loopFrame = (frame - delay + 750) % 75;
  const radius = interpolate(loopFrame, [0, 75], [30, 120], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(loopFrame, [0, 75], [0.6, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        width: radius * 2,
        height: radius * 2,
        borderRadius: "50%",
        border: `2px solid ${COLORS.skyBlue}`,
        opacity,
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
      }}
    />
  );
};

/** Audio waveform bars */
const Waveform: React.FC<{ frame: number }> = ({ frame }) => {
  const bars = 30;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 3,
        height: 160,
      }}
    >
      {Array.from({ length: bars }).map((_, i) => {
        const baseHeight =
          20 + 50 * Math.abs(Math.sin(frame * 0.12 + i * 0.5));
        const height = Math.max(6, baseHeight);
        return (
          <div
            key={i}
            style={{
              width: 5,
              height,
              borderRadius: 3,
              background: `linear-gradient(to top, ${COLORS.skyBlue}, ${COLORS.violet})`,
              opacity: 0.85,
            }}
          />
        );
      })}
    </div>
  );
};

/* ── transcript data ── */

interface Message {
  isAgent: boolean;
  text: string;
  time: string;
  appearFrame: number;
}

const TRANSCRIPT: Message[] = [
  {
    isAgent: true,
    text: "Hi, I'm calling to cancel subscription for account 12345.",
    time: "00:01:12",
    appearFrame: 10,
  },
  {
    isAgent: false,
    text: "I can help with that. Let me pull up your account.",
    time: "00:01:18",
    appearFrame: 70,
  },
  {
    isAgent: true,
    text: "Thank you.",
    time: "00:01:24",
    appearFrame: 120,
  },
  {
    isAgent: false,
    text: "Account located. Processing cancellation and $49.99 refund.",
    time: "00:01:32",
    appearFrame: 160,
  },
];

/* ── IVR menu items ── */

interface MenuItem {
  num: string;
  label: string;
}

const IVR_MENU: MenuItem[] = [
  { num: "1", label: "Billing" },
  { num: "2", label: "Technical Support" },
  { num: "3", label: "Cancel / Modify Account" },
];

/* ── main component ── */

export const CallScene: React.FC = () => {
  const frame = useCurrentFrame();

  // card entrance spring
  const cardScale = spring({
    frame,
    fps: 30,
    config: { damping: 200, stiffness: 100, mass: 0.8 },
    from: 0.92,
    to: 1,
    durationInFrames: 20,
  });

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily,
        background: `radial-gradient(ellipse at center, #0d1117 0%, #060810 100%)`,
        position: "relative",
      }}
    >
      {/* ── Main card ── */}
      <div
        style={{
          width: 1200,
          height: 700,
          background: "#141825",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 20,
          boxShadow: "0 40px 100px rgba(0,0,0,0.6)",
          transform: `scale(${cardScale})`,
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* Phase 1: Dialing (0-119) */}
        <Sequence from={0} durationInFrames={120} layout="none">
          <DialingPhase />
        </Sequence>

        {/* Phase 2: IVR (120-299) */}
        <Sequence from={120} durationInFrames={180} layout="none">
          <IVRPhase />
        </Sequence>

        {/* Phase 3: Transcript (300-539) */}
        <Sequence from={300} durationInFrames={240} layout="none">
          <TranscriptPhase />
        </Sequence>

        {/* Phase 4: Approval overlay (540-599) */}
        <Sequence from={540} durationInFrames={60} layout="none">
          <ApprovalPhase />
        </Sequence>
      </div>
    </div>
  );
};

/* ── Phase 1: Dialing ── */

const DialingPhase: React.FC = () => {
  const frame = useCurrentFrame();

  const phoneNumber = "+1 (800) 288-2020";
  const typedCount = typewriterCount(frame, phoneNumber.length, 40);
  const displayNumber = phoneNumber.slice(0, typedCount);
  const connectingOpacity = 0.4 + 0.6 * pulse(frame, 0.1);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 36,
      }}
    >
      {/* label */}
      <div
        style={{
          fontSize: 14,
          fontWeight: 700,
          letterSpacing: 5,
          color: COLORS.gray400,
          textTransform: "uppercase",
          opacity: fadeIn(frame, 0, 15),
        }}
      >
        OUTBOUND CALL
      </div>

      {/* phone number */}
      <div
        style={{
          fontSize: 56,
          fontFamily: monoFamily,
          color: COLORS.white,
          letterSpacing: 2,
          minHeight: 68,
        }}
      >
        {displayNumber}
      </div>

      {/* service name */}
      <div
        style={{
          fontSize: 20,
          color: COLORS.gray400,
          opacity: fadeIn(frame, 30, 15),
        }}
      >
        AT&T Customer Service
      </div>

      {/* ring indicator */}
      <div
        style={{
          position: "relative",
          width: 240,
          height: 240,
        }}
      >
        <DialRing frame={frame} delay={0} />
        <DialRing frame={frame} delay={25} />
        <DialRing frame={frame} delay={50} />
        {/* center dot */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 16,
            height: 16,
            borderRadius: "50%",
            background: COLORS.skyBlue,
            boxShadow: `0 0 24px ${COLORS.skyBlue}60, 0 0 60px ${COLORS.skyBlue}30`,
          }}
        />
      </div>

      {/* connecting text */}
      <div
        style={{
          fontSize: 18,
          color: COLORS.gray400,
          opacity: connectingOpacity,
        }}
      >
        Connecting...
      </div>
    </div>
  );
};

/* ── Phase 2: IVR Navigation ── */

const IVRPhase: React.FC = () => {
  const frame = useCurrentFrame();

  const highlightItem3 = frame >= 60;
  const showDTMF = frame >= 60 && frame < 100;
  const showSubMenu = frame >= 120;
  const showConnected = frame >= 150;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 24,
        padding: 48,
      }}
    >
      {/* header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginBottom: 12,
        }}
      >
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: COLORS.amber,
            boxShadow: `0 0 10px ${COLORS.amber}80`,
          }}
        />
        <span
          style={{
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: 5,
            color: COLORS.gray400,
            textTransform: "uppercase",
          }}
        >
          IVR MENU DETECTED
        </span>
      </div>

      {/* menu items */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 24,
          alignItems: "center",
        }}
      >
        {IVR_MENU.map((item, i) => {
          const s = stagger(frame, i, 12, 20);
          const isHighlighted = i === 2 && highlightItem3;

          return (
            <div
              key={item.num}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                opacity: s.opacity,
                transform: `translateY(${s.y}px)`,
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 16,
                  fontWeight: 700,
                  border: isHighlighted
                    ? "none"
                    : `1px solid ${COLORS.gray600}`,
                  background: isHighlighted ? COLORS.emerald : "transparent",
                  color: isHighlighted ? COLORS.white : COLORS.gray400,
                  boxShadow: isHighlighted
                    ? `0 0 16px ${COLORS.emerald}40`
                    : "none",
                }}
              >
                {item.num}
              </div>
              <span
                style={{
                  fontSize: 22,
                  color: isHighlighted ? COLORS.white : COLORS.gray400,
                }}
              >
                {item.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* DTMF indicator */}
      {showDTMF && (
        <div
          style={{
            fontSize: 16,
            color: COLORS.emerald,
            opacity: fadeIn(frame, 60, 10),
          }}
        >
          Pressing 3...
        </div>
      )}

      {/* sub-menu */}
      {showSubMenu && !showConnected && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            opacity: fadeIn(frame, 120, 15),
            transform: `translateY(${slideUp(frame, 120, 15, 20)}px)`,
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 16,
              fontWeight: 700,
              background: COLORS.emerald,
              color: COLORS.white,
              boxShadow: `0 0 16px ${COLORS.emerald}40`,
            }}
          >
            1
          </div>
          <span style={{ fontSize: 22, color: COLORS.white }}>
            Confirm cancellation
          </span>
        </div>
      )}

      {/* connected to representative */}
      {showConnected && (
        <div
          style={{
            fontSize: 22,
            color: COLORS.emerald,
            fontWeight: 700,
            opacity: fadeIn(frame, 150, 15),
            transform: `translateY(${slideUp(frame, 150, 15, 20)}px)`,
          }}
        >
          Connected to representative
        </div>
      )}
    </div>
  );
};

/* ── Phase 3: Live Transcript ── */

const TranscriptPhase: React.FC = () => {
  const frame = useCurrentFrame();

  // determine which agent is "speaking" for waveform indicator
  const activeSpeaker =
    frame < 60
      ? "agent"
      : frame < 110
        ? "rep"
        : frame < 140
          ? "agent"
          : "rep";
  const isAgentSpeaking = activeSpeaker === "agent";

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
      }}
    >
      {/* left: waveform (35%) */}
      <div
        style={{
          width: "35%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          borderRight: "1px solid rgba(255,255,255,0.06)",
          padding: 32,
          gap: 20,
        }}
      >
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: 4,
            color: COLORS.gray500,
            textTransform: "uppercase",
          }}
        >
          LIVE AUDIO
        </div>
        <Waveform frame={frame} />
        <div
          style={{
            fontSize: 15,
            color: isAgentSpeaking ? COLORS.skyBlue : COLORS.gray400,
          }}
        >
          {isAgentSpeaking ? "Agent speaking" : "Rep speaking"}
        </div>
      </div>

      {/* right: transcript (65%) */}
      <div
        style={{
          width: "65%",
          padding: "36px 40px",
          display: "flex",
          flexDirection: "column",
          gap: 0,
          overflowY: "hidden",
        }}
      >
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: 4,
            color: COLORS.gray500,
            textTransform: "uppercase",
            marginBottom: 24,
          }}
        >
          TRANSCRIPT
        </div>

        {TRANSCRIPT.map((msg, i) => {
          if (frame < msg.appearFrame) return null;
          const localF = frame - msg.appearFrame;
          const opacity = interpolate(localF, [0, 15], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const y = interpolate(localF, [0, 15], [20, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          return (
            <div
              key={i}
              style={{
                opacity,
                transform: `translateY(${y}px)`,
                padding: "16px 0",
                borderBottom:
                  i < TRANSCRIPT.length - 1
                    ? "1px solid rgba(255,255,255,0.05)"
                    : "none",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 14,
                }}
              >
                {/* accent bar */}
                <div
                  style={{
                    width: 4,
                    minHeight: 44,
                    borderRadius: 2,
                    background: msg.isAgent ? COLORS.skyBlue : COLORS.gray500,
                    flexShrink: 0,
                    marginTop: 2,
                  }}
                />
                <div>
                  <div
                    style={{
                      fontSize: 13,
                      color: COLORS.gray500,
                      marginBottom: 6,
                      display: "flex",
                      gap: 10,
                      alignItems: "center",
                    }}
                  >
                    <span>{msg.isAgent ? "Agent" : "Rep"}</span>
                    <span style={{ fontSize: 12, color: COLORS.gray600 }}>
                      {msg.time}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: 16,
                      color: COLORS.gray200,
                      lineHeight: 1.5,
                    }}
                  >
                    {msg.text}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/* ── Phase 4: Approval Flow ── */

const ApprovalPhase: React.FC = () => {
  const frame = useCurrentFrame();

  // backdrop fade in
  const backdropOpacity = fadeIn(frame, 0, 10);

  // card spring from bottom
  const cardY = spring({
    frame,
    fps: 30,
    config: { damping: 15, stiffness: 80, mass: 0.6 },
    from: 500,
    to: 0,
    durationInFrames: 30,
  });

  // approve glow at frame 30
  const approveGlow = frame >= 30 && frame < 40;
  // border flash
  const borderFlash = frame >= 30 && frame < 35;
  // approved state at frame 40
  const showApproved = frame >= 40;
  const approvedOpacity = fadeIn(frame, 40, 10);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 10,
      }}
    >
      {/* backdrop */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(0,0,0,0.7)",
          opacity: backdropOpacity,
        }}
      />

      {/* approval card */}
      <div
        style={{
          position: "relative",
          width: 520,
          background: "#1e293b",
          border: borderFlash
            ? `2px solid ${COLORS.emerald}`
            : "1px solid rgba(255,255,255,0.1)",
          borderRadius: 20,
          boxShadow: borderFlash
            ? glowShadow(COLORS.emerald, 1.5)
            : "0 30px 80px rgba(0,0,0,0.5)",
          transform: `translateY(${cardY}px)`,
          overflow: "hidden",
        }}
      >
        {!showApproved ? (
          <div style={{ padding: "32px 36px" }}>
            {/* header */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                marginBottom: 18,
              }}
            >
              <span style={{ fontSize: 22 }}>🔒</span>
              <span
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: COLORS.white,
                }}
              >
                Approval Required
              </span>
            </div>

            {/* body */}
            <div
              style={{
                fontSize: 18,
                color: COLORS.gray200,
                lineHeight: 1.5,
                marginBottom: 24,
              }}
            >
              Cancel subscription and process $49.99 refund?
            </div>

            {/* divider */}
            <div
              style={{
                height: 1,
                background: "rgba(255,255,255,0.08)",
                marginBottom: 24,
              }}
            />

            {/* buttons */}
            <div
              style={{ display: "flex", gap: 14, justifyContent: "flex-end" }}
            >
              <div
                style={{
                  padding: "14px 40px",
                  borderRadius: 10,
                  border: `1px solid ${COLORS.gray600}`,
                  color: COLORS.gray400,
                  fontSize: 16,
                  fontWeight: 700,
                }}
              >
                Decline
              </div>
              <div
                style={{
                  padding: "14px 40px",
                  borderRadius: 10,
                  background: COLORS.emerald,
                  color: COLORS.white,
                  fontSize: 16,
                  fontWeight: 700,
                  boxShadow: approveGlow
                    ? glowShadow(COLORS.emerald, 2)
                    : "none",
                }}
              >
                Approve
              </div>
            </div>
          </div>
        ) : (
          <div
            style={{
              padding: "70px 36px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              opacity: approvedOpacity,
            }}
          >
            <span
              style={{
                fontSize: 42,
                fontWeight: 700,
                color: COLORS.emerald,
                textShadow: `0 0 40px ${COLORS.emerald}40`,
              }}
            >
              ✓ Approved
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default CallScene;
