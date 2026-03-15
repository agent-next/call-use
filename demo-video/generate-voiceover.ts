import { writeFileSync, mkdirSync, existsSync } from "fs";

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
if (!OPENAI_API_KEY) {
  console.error("Error: OPENAI_API_KEY environment variable is required.");
  process.exit(1);
}

const VOICE = "onyx"; // deep, professional male voice

const SCENES = [
  {
    id: "scene-01-pain",
    text: "You've been on hold for 47 minutes. The music loops. The robot asks you to press 1... again.",
  },
  {
    id: "scene-02-turn",
    text: "What if your AI agent could handle this for you?",
  },
  {
    id: "scene-03-agent",
    text: "Just tell your agent what you need. It picks up the phone and gets to work.",
  },
  {
    id: "scene-04-call",
    text: "It navigates the menu, talks to a real person, and gets your refund approved — all on its own.",
  },
  {
    id: "scene-05-result",
    text: "Done. Full transcript. Structured outcome. Two minutes flat.",
  },
  {
    id: "scene-06-cta",
    text: "call-use. Let your AI agent handle the call.",
  },
];

async function generateVoiceover(id: string, text: string): Promise<void> {
  console.log(`Generating ${id}...`);
  const response = await fetch("https://api.openai.com/v1/audio/speech", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-4o-mini-tts",
      voice: VOICE,
      input: text,
      response_format: "mp3",
    }),
  });
  if (!response.ok) {
    const err = await response.text();
    throw new Error(`OpenAI TTS error for ${id}: ${response.status} ${err}`);
  }
  const buf = Buffer.from(await response.arrayBuffer());
  writeFileSync(`public/voiceover/${id}.mp3`, buf);
  console.log(`  ✓ ${id}.mp3 (${buf.length} bytes)`);
}

async function main() {
  if (!existsSync("public/voiceover"))
    mkdirSync("public/voiceover", { recursive: true });
  for (const s of SCENES) await generateVoiceover(s.id, s.text);
  console.log("\n✅ Done! Run `npm start` to preview.");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
