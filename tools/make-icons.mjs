// Regenerates PNG icons from tools/logo.svg (placeholder Remoto mark).
// Usage: npm i --no-save sharp && node tools/make-icons.mjs
import sharp from "sharp";
import { copyFileSync } from "node:fs";

const src = new URL("./logo.svg", import.meta.url).pathname;
const out = new URL("../custom_components/remoto_branding/www/icons/", import.meta.url).pathname;

const sizes = { "favicon.png": 64, "apple-touch-icon.png": 180, "icon-192.png": 192, "icon-512.png": 512 };
for (const [name, size] of Object.entries(sizes)) {
  await sharp(src, { density: 300 }).resize(size, size).png().toFile(out + name);
}
// Maskable: logo shrunk into the 80% safe zone on a solid background.
const inner = await sharp(src, { density: 300 }).resize(410, 410).png().toBuffer();
await sharp({ create: { width: 512, height: 512, channels: 4, background: "#0B6E4F" } })
  .composite([{ input: inner, gravity: "center" }])
  .png()
  .toFile(out + "icon-512-maskable.png");
copyFileSync(src, out + "logo.svg");
console.log("icons written to", out);
