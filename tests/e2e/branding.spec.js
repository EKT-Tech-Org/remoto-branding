import { test, expect } from "@playwright/test";

const CLIENT = { username: "client", password: "remoto-client-pass" };
const UPSTREAM = /Home\s?Assistant/i;
// Pages a non-admin client can reach.
const PAGES = ["/lovelace/0", "/map", "/logbook", "/history", "/profile/general"];

// innerText does not cross shadow roots, so collect visible text manually.
const deepText = () => {
  const out = [];
  const visit = (root) => {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    for (let n = walker.currentNode; n; n = walker.nextNode()) {
      if (n.nodeType === Node.TEXT_NODE) {
        const el = n.parentElement;
        if (el && !["SCRIPT", "STYLE"].includes(el.tagName) && el.offsetParent !== null) out.push(n.data);
      } else {
        for (const a of ["title", "aria-label", "placeholder", "alt"]) {
          const v = n.getAttribute?.(a);
          if (v) out.push(v);
        }
        if (n.shadowRoot) visit(n.shadowRoot);
      }
    }
  };
  visit(document.documentElement);
  return out.join("\n");
};

const login = async (page) => {
  await page.goto("/");
  await page.getByLabel(/username/i).fill(CLIENT.username);
  await page.getByLabel(/password/i).fill(CLIENT.password);
  await page.getByRole("button", { name: /log in/i }).click();
  await page.waitForURL((url) => !url.pathname.startsWith("/auth"));
  await page.waitForTimeout(1500);
};

test("login page is rebranded", async ({ page }) => {
  await page.goto("/");
  await page.waitForURL(/\/auth\/authorize/);
  await page.getByLabel(/username/i).waitFor();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: "test-results/login.png", fullPage: true });
  // Soft: the login page may not load extra frontend modules on every release.
  expect.soft(await page.title()).not.toMatch(UPSTREAM);
  expect.soft(await page.evaluate(deepText)).not.toMatch(UPSTREAM);
});

test("client pages show Remoto branding only", async ({ page }) => {
  const scriptErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error" && msg.text().includes("remoto")) scriptErrors.push(msg.text());
  });
  await login(page);

  const manifest = await page.locator('link[rel="manifest"]').getAttribute("href");
  expect(manifest).toContain("/remoto/manifest.json");
  expect(await page.locator('meta[name="apple-mobile-web-app-title"]').getAttribute("content")).toBe("Remoto");

  for (const path of PAGES) {
    await page.goto(path);
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `test-results/page${path.replaceAll("/", "_")}.png`, fullPage: true });
    expect(await page.title(), `title on ${path}`).not.toMatch(UPSTREAM);
    const text = await page.evaluate(deepText);
    const hit = text.split("\n").find((l) => UPSTREAM.test(l));
    expect(hit, `visible upstream name on ${path}`).toBeUndefined();
  }
  expect(scriptErrors).toEqual([]);
});
