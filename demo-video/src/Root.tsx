import { Composition } from "remotion";
import { CallUseDemo, CallUseDemoSchema } from "./CallUseDemo";
import { FPS } from "./lib/theme";

// 6 scenes: 10+5+15+20+5+5 = 60s = 1800 frames
// 5 transitions × 10 frames = 50 frames overlap
// Effective: 1800 - 50 = 1750 frames (~58.3s)
const DURATION = 1800 - 5 * 10;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CallUseDemo"
      component={CallUseDemo}
      durationInFrames={DURATION}
      fps={FPS}
      width={1920}
      height={1080}
      schema={CallUseDemoSchema}
      defaultProps={{
        phoneNumber: "+18001234567",
        instructions: "Cancel my subscription",
        githubUrl: "github.com/agent-next/call-use",
        showApprovalFlow: true,
      }}
    />
  );
};
