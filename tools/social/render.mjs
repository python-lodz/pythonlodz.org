// tools/social/render.mjs
// Renderuje szablony HTML (tools/social/templates) do PNG w formatach 4:5 / 1:1 / 16:9.
// Użycie: node tools/social/render.mjs <job.json>
// Wzorzec: dumtek/fb-ads-system/scripts/render_ad_mockups.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const __dir = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dir, "../..");
const CHROME = process.env.CHROME_BIN || "/usr/bin/google-chrome-stable";

const FORMATS = { "4x5": [1080, 1350], "1x1": [1080, 1080], "16x9": [1920, 1080] };

const b64 = (file, mime) =>
  `data:${mime};base64,` + fs.readFileSync(file).toString("base64");

const jobPath = process.argv[2];
if (!jobPath) {
  console.error("Użycie: node tools/social/render.mjs <job.json>");
  process.exit(1);
}
const job = JSON.parse(fs.readFileSync(jobPath, "utf8"));
const template = fs.readFileSync(
  path.join(__dir, "templates", `${job.template}.html`),
  "utf8",
);

const replacements = {
  ...job.fields,
  LOGO: b64(path.join(ROOT, "page/assets/images/logo.png"), "image/png"),
  FONT_REGULAR: b64(
    path.join(ROOT, "page/assets/fonts/OpenSans-Regular.ttf"),
    "font/ttf",
  ),
  FONT_BOLD: b64(
    path.join(ROOT, "page/assets/fonts/OpenSans-ExtraBold.ttf"),
    "font/ttf",
  ),
  BACKGROUND: job.background
    ? b64(path.resolve(ROOT, job.background), "image/jpeg")
    : "",
  CUTOUT: job.cutout ? b64(path.resolve(ROOT, job.cutout), "image/png") : "",
};

function fill(html, extra) {
  let out = html;
  for (const [key, value] of Object.entries({ ...replacements, ...extra })) {
    out = out.replaceAll(`{{${key}}}`, String(value));
  }
  return out;
}

const outDir = path.resolve(ROOT, job.outDir);
fs.mkdirSync(outDir, { recursive: true });
const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: "new",
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});
for (const format of job.formats) {
  const [width, height] = FORMATS[format];
  const page = await browser.newPage();
  await page.setViewport({ width, height, deviceScaleFactor: 1 });
  await page.setContent(
    fill(template, { WIDTH: width, HEIGHT: height, FORMAT: format }),
    { waitUntil: "networkidle0" },
  );
  const out = path.join(outDir, `${job.name}-${format}.png`);
  await page.screenshot({ path: out });
  console.log("zapisano", out);
  await page.close();
}
await browser.close();
console.log("GOTOWE");
