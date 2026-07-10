// tools/social/mockup.mjs
// Makieta organicznego posta w feedzie FB — do akceptacji grafik i tekstów (gk-sm-3).
// Użycie: node tools/social/mockup.mjs <grafika.png> <plik-z-tekstem> <out.png>
// Wzorzec: dumtek/fb-ads-system/scripts/render_ad_mockups.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const __dir = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dir, "../..");
const CHROME = process.env.CHROME_BIN || "/usr/bin/google-chrome-stable";
const LOGO = path.join(ROOT, "page/assets/images/logo.png");

const [imagePath, textPath, outPath] = process.argv.slice(2);
if (!outPath) {
  console.error(
    "Użycie: node tools/social/mockup.mjs <grafika.png> <tekst.md> <out.png>",
  );
  process.exit(1);
}

const b64 = (p) => "data:image/png;base64," + fs.readFileSync(p).toString("base64");
const esc = (s) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const body = fs.readFileSync(textPath, "utf8").trim();

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#fff;font-family:Helvetica,Arial,'Segoe UI',sans-serif;-webkit-font-smoothing:antialiased}
  .card{width:500px;background:#fff;border:1px solid #dadde1}
  .hd{display:flex;align-items:center;padding:12px 12px 8px}
  .av{width:40px;height:40px;border-radius:50%;object-fit:cover;background:#001F3F;border:1px solid #ddd}
  .who{margin-left:8px;flex:1;line-height:1.3}
  .nm{font-weight:600;font-size:15px;color:#050505}
  .sb{font-size:12px;color:#65676b;display:flex;align-items:center;gap:4px}
  .dots{color:#65676b;font-size:20px;padding:0 4px}
  .tx{padding:0 12px 10px;font-size:15px;line-height:1.4;color:#050505;white-space:pre-wrap}
  .img{width:100%;display:block}
  .rx{display:flex;justify-content:space-around;border-top:1px solid #ced0d4;padding:6px 0;
      color:#65676b;font-size:14px;font-weight:600}
</style></head><body>
<div class="card" id="card">
  <div class="hd">
    <img class="av" src="${b64(LOGO)}">
    <div class="who"><div class="nm">Python Łódź</div>
      <div class="sb">2 godz. · <span>🌐</span></div></div>
    <div class="dots">···</div>
  </div>
  <div class="tx">${esc(body)}</div>
  <img class="img" src="${b64(imagePath)}">
  <div class="rx"><span>👍 Lubię to!</span><span>💬 Komentarz</span><span>↪ Udostępnij</span></div>
</div></body></html>`;

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: "new",
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 500, height: 900, deviceScaleFactor: 2 });
await page.setContent(html, { waitUntil: "networkidle0" });
const el = await page.$("#card");
await el.screenshot({ path: outPath });
await browser.close();
console.log("zapisano", outPath);
