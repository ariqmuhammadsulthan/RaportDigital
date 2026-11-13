// Real Flask/SQLite fixture under a URL prefix; synthetic records only.
const assert = require("node:assert/strict");
const fs = require("node:fs"), os = require("node:os"), path = require("node:path");
const { spawn } = require("node:child_process");
const { once } = require("node:events");
const { createInterface } = require("node:readline");
const playwright = require(process.env.RAPOR_PLAYWRIGHT || "playwright");
const repo = path.resolve(__dirname, "..");

(async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "raportdigital-test-"));
  const child = spawn(process.env.PYTHON_BIN || "python", [path.join(__dirname, "browser_server.py"), directory], {
    cwd: repo, env: { ...process.env, PYTHONPATH: repo, RAPOR_TRUSTED_HOSTS: "" },
    stdio: ["ignore", "pipe", "inherit"], windowsHide: true,
  });
  const exit = once(child, "exit");
  let browser;
  try {
    const lines = createInterface({ input: child.stdout });
    const ready = await Promise.race([
      once(lines, "line").then(([line]) => JSON.parse(line)),
      exit.then(() => { throw Error("Fixture server exited before readiness"); }),
      new Promise((_, reject) => {
        const timer = setTimeout(() => reject(Error("Fixture server did not start")), 15000);
        timer.unref();
      }),
    ]);
    lines.close();
    const kind = process.env.RAPOR_BROWSER || "chromium";
    browser = await playwright[kind].launch(kind === "chromium" && process.env.RAPOR_CHROMIUM
      ? { executablePath: process.env.RAPOR_CHROMIUM } : {});
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    page.on("dialog", dialog => dialog.accept());
    const origin = `http://127.0.0.1:${ready.port}/grades`;
    await page.goto(origin + "/");
    await page.locator('[name="name"]').fill("fixture");
    await page.locator('[name="password"]').fill(ready.password);
    await Promise.all([page.waitForURL(origin + "/"), page.locator("button.primary").click()]);
    for (const program of ["a", "b", "c-ips", "c-ipa"]) {
      await page.goto(`${origin}/book/${program}/2026`);
      await page.waitForSelector('[data-w="wali"]');
      assert.equal(await page.locator('[data-p="nama"]').inputValue(), "");
      assert.equal(await page.evaluate(() => document.body.dataset.endpoint.startsWith("/grades/api/")), true);
    }
    await page.locator('[data-p="nama"]').fill("Sekolah Contoh");
    await page.locator('[data-w="wali"]').fill("Guru Uji");
    await page.locator('[data-x="tgl"]').fill("13 November 2026");
    await page.click("#b2");
    await page.locator('[data-r="0"][data-c="0"]').fill("Siswa Uji");
    await page.selectOption("#columns", "marks");
    await page.locator('[data-r="0"][data-c="1"]').evaluate(el => {
      const data = new DataTransfer();
      data.setData("text/plain", allM().map((_, i) => i === 0 ? "0" : "80").join("\t"));
      const event = new ClipboardEvent("paste", { bubbles: true, cancelable: true });
      Object.defineProperty(event, "clipboardData", { value: data });
      el.dispatchEvent(event);
    });
    await page.waitForFunction(() => !dirty && !pending && revision > 0);
    assert.equal(await page.evaluate(() => D().st[0].n.Ganjil.u0), "0");
    await page.reload();
    await page.waitForSelector("#work");
    assert.equal(await page.evaluate(() => D().st[0].nama), "Siswa Uji");
    await page.setViewportSize({ width: 390, height: 844 });
    await page.click("#b3");
    assert.equal(await page.locator("#issue").isEnabled(), true);
    assert.match(await page.locator("#sheet").innerText(), /Telepon/);
    assert.doesNotMatch(await page.locator("#sheet").innerText(), /Telephon/);
    const issued = page.waitForURL(/\/grades\/issued\/\d+$/);
    await page.click("#issue");
    await issued;
    await page.waitForSelector("#sheet .pg");
    assert.equal(await page.locator("#issue").isVisible(), false);
    assert.match(await page.locator(".pg").first().getAttribute("data-stamp"), /Arsip #/);
    await page.emulateMedia({ media: "print" });
    assert.equal(await page.locator("#sheet .pg").first().isVisible(), true);
    await page.emulateMedia({ media: "screen" });
    await page.locator("#leave button").click();
    await page.waitForURL(origin + "/login");
    assert.deepEqual(errors, []);
    console.log(`${kind}: mounted login, all programs, blank defaults, autosave/reload, Excel paste/zero, mobile preview, issue, print media and logout passed.`);
  } finally {
    if (browser) await browser.close();
    if (child.exitCode === null) child.kill();
    await exit;
    const resolved = path.resolve(directory);
    if (path.dirname(resolved) !== path.resolve(os.tmpdir()) || !path.basename(resolved).startsWith("raportdigital-test-"))
      throw Error("Unexpected fixture cleanup path");
    fs.rmSync(resolved, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
