// Remoto Branding: rewrites visible upstream branding in the frontend.
// It only touches text, attributes and <head> tags, never internal component
// APIs, so upstream releases rarely break it. Every step is wrapped in try/catch:
// if something fails, the stock UI keeps working.

const params = new URL(import.meta.url).searchParams;
const BRAND = params.get("name") || "Remoto";
const COLOR = params.get("color") || "#553D9F";
const VERSION = params.get("v") || "0";
const BASE = "/remoto";

const UPSTREAM = /Home[\s ]?Assistant/g;
const ATTRS = ["title", "aria-label", "placeholder", "alt", "label", "heading", "header"];
const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "TEXTAREA", "CODE", "PRE", "HA-CODE-EDITOR"]);
const LOGO_SRC = /\/static\/icons\/|home-assistant|\/static\/images\/logo/;
// Help / docs links that point at upstream sites are hidden.
const UPSTREAM_LINK = /home-assistant\.io|nabucasa\.com|openhomefoundation\.org/;

const safe = (fn) => {
  try {
    fn();
  } catch (err) {
    console.debug("[remoto] skipped:", err);
  }
};

const rebrand = (value) => value.replace(UPSTREAM, BRAND);

// ---------- <head>: title, icons, PWA manifest ----------

const setLink = (rel, href, extra = {}) => {
  let el = document.head.querySelector(`link[rel="${rel}"]`);
  if (!el) {
    el = document.createElement("link");
    el.rel = rel;
    document.head.appendChild(el);
  }
  if (el.getAttribute("href") !== href) el.setAttribute("href", href);
  for (const [k, v] of Object.entries(extra)) el.setAttribute(k, v);
};

const setMeta = (name, content) => {
  let el = document.head.querySelector(`meta[name="${name}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.name = name;
    document.head.appendChild(el);
  }
  if (el.content !== content) el.content = content;
};

const brandHead = () => {
  const v = `?v=${VERSION}`;
  for (const el of document.head.querySelectorAll('link[rel~="icon"], link[rel="mask-icon"]')) {
    if (!el.href.includes(BASE)) el.remove();
  }
  setLink("icon", `${BASE}/icons/favicon.svg${v}`, { type: "image/svg+xml" });
  setLink("apple-touch-icon", `${BASE}/icons/apple-touch-icon.png${v}`);
  setLink("manifest", `${BASE}/manifest.json${v}`, { crossorigin: "use-credentials" });
  setMeta("apple-mobile-web-app-title", BRAND);
  setMeta("application-name", BRAND);
  setMeta("theme-color", COLOR);
};

const brandTitle = () => {
  const t = document.title;
  if (!t) {
    document.title = BRAND;
    return;
  }
  const next = rebrand(t);
  if (next !== t) document.title = next;
};

// ---------- body: text nodes and attributes, including shadow roots ----------

const observed = new WeakSet();
let pending = new Set();
let scheduled = false;

const brandElement = (el) => {
  for (const attr of ATTRS) {
    const val = el.getAttribute?.(attr);
    if (val && UPSTREAM.test(val)) el.setAttribute(attr, rebrand(val));
    UPSTREAM.lastIndex = 0;
  }
  if (el.tagName === "IMG" && LOGO_SRC.test(el.getAttribute("src") || "")) {
    el.src = `${BASE}/icons/logo.svg?v=${VERSION}`;
  }
  if (el.tagName === "A" && UPSTREAM_LINK.test(el.getAttribute("href") || "")) {
    el.style.display = "none";
  }
};

const walk = (root) => {
  const walker = document.createTreeWalker(
    root,
    NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT
  );
  let node = root.nodeType === Node.ELEMENT_NODE ? root : walker.nextNode();
  while (node) {
    if (node.nodeType === Node.TEXT_NODE) {
      const parent = node.parentNode;
      if (!(parent && SKIP_TAGS.has(parent.nodeName)) && UPSTREAM.test(node.data)) {
        node.data = rebrand(node.data);
      }
      UPSTREAM.lastIndex = 0;
    } else {
      if (SKIP_TAGS.has(node.nodeName)) {
        node = walker.nextSibling() || walker.nextNode();
        continue;
      }
      brandElement(node);
      if (node.shadowRoot) {
        observe(node.shadowRoot);
        walk(node.shadowRoot);
      }
    }
    node = walker.nextNode();
  }
};

const flush = () => {
  scheduled = false;
  const roots = pending;
  pending = new Set();
  for (const root of roots) safe(() => walk(root));
  safe(brandTitle);
};

const queue = (node) => {
  pending.add(node);
  if (!scheduled) {
    scheduled = true;
    requestAnimationFrame(flush);
  }
};

const onMutations = (mutations) => {
  for (const m of mutations) {
    if (m.type === "characterData") queue(m.target.parentNode || m.target);
    else if (m.type === "attributes") queue(m.target);
    else for (const n of m.addedNodes) queue(n.nodeType === Node.TEXT_NODE ? n.parentNode || n : n);
  }
};

function observe(root) {
  if (observed.has(root)) return;
  observed.add(root);
  new MutationObserver(onMutations).observe(root, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: ATTRS.concat("src", "href"),
  });
}

// Shadow roots attached after this script runs get observed immediately.
const origAttach = Element.prototype.attachShadow;
Element.prototype.attachShadow = function (init) {
  const root = origAttach.call(this, init);
  safe(() => {
    observe(root);
    queue(root);
  });
  return root;
};

// ---------- theme color ----------

const brandColors = () => {
  const style = document.createElement("style");
  style.id = "remoto-branding";
  style.textContent = `:root{--remoto-primary:${COLOR};}.ohf-logo{display:none!important}`;
  document.head.appendChild(style);
};

// ---------- boot ----------

safe(brandHead);
safe(brandTitle);
safe(brandColors);
safe(() => {
  observe(document.documentElement);
  new MutationObserver(() => safe(brandTitle)).observe(document.head, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  // The frontend re-adds its own icon/manifest links on some navigations.
  new MutationObserver(() => safe(brandHead)).observe(document.head, { childList: true });
  queue(document.documentElement);
});
