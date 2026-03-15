import { AbsoluteFill, Sequence, staticFile, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";
import { z } from "zod";
import { PainScene } from "./scenes/PainScene";
import { TurnScene } from "./scenes/TurnScene";
import { CodeScene } from "./scenes/CodeScene";
import { CallScene } from "./scenes/CallScene";
import { ResultScene } from "./scenes/ResultScene";
import { CTAScene } from "./scenes/CTAScene";

export const CallUseDemoSchema = z.object({
  phoneNumber: z.string().default("+18001234567"),
  instructions: z.string().default("Cancel my subscription"),
  githubUrl: z.string().default("github.com/agent-next/call-use"),
  showApprovalFlow: z.boolean().default(true),
});

export type CallUseDemoProps = z.infer<typeof CallUseDemoSchema>;

const FADE = 10; // short fade to minimize scene overlap

export const CallUseDemo: React.FC<CallUseDemoProps> = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background music — fades in and out */}
      <Audio
        src={staticFile("bgm.mp3")}
        volume={(f) => {
          const fadeInEnd = 2 * fps;
          const fadeOutStart = 1750 - 3 * fps;
          if (f < fadeInEnd) return (f / fadeInEnd) * 0.15;
          if (f > fadeOutStart) return Math.max(0, (1750 - f) / (3 * fps)) * 0.15;
          return 0.15;
        }}
      />
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={10 * fps}>
          <PainScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: FADE })}
        />

        <TransitionSeries.Sequence durationInFrames={5 * fps}>
          <TurnScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: FADE })}
        />

        <TransitionSeries.Sequence durationInFrames={15 * fps}>
          <CodeScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={wipe({ direction: "from-left" })}
          timing={linearTiming({ durationInFrames: FADE })}
        />

        <TransitionSeries.Sequence durationInFrames={20 * fps}>
          <CallScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: FADE })}
        />

        <TransitionSeries.Sequence durationInFrames={5 * fps}>
          <ResultScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: FADE })}
        />

        <TransitionSeries.Sequence durationInFrames={5 * fps}>
          <CTAScene />
        </TransitionSeries.Sequence>
      </TransitionSeries>

      {/* Voiceover tracks — timed to scene starts (FADE=10) */}
      <Sequence from={0} layout="none">
        <Audio src={staticFile("voiceover/scene-01-pain.mp3")} volume={0.9} />
      </Sequence>
      <Sequence from={290} layout="none">
        <Audio src={staticFile("voiceover/scene-02-turn.mp3")} volume={0.9} />
      </Sequence>
      <Sequence from={430} layout="none">
        <Audio src={staticFile("voiceover/scene-03-agent.mp3")} volume={0.9} />
      </Sequence>
      <Sequence from={870} layout="none">
        <Audio src={staticFile("voiceover/scene-04-call.mp3")} volume={0.9} />
      </Sequence>
      <Sequence from={1460} layout="none">
        <Audio src={staticFile("voiceover/scene-05-result.mp3")} volume={0.9} />
      </Sequence>
      <Sequence from={1600} layout="none">
        <Audio src={staticFile("voiceover/scene-06-cta.mp3")} volume={0.9} />
      </Sequence>
    </AbsoluteFill>
  );
};
