// Prepares an instance for the branding checks and verifies the auto-setup.
// Onboards it (or logs in if it already is), then checks that Remoto Branding
// configured itself, that the Remoto theme is the default, and creates a
// non-admin client user.
// Env: HA_URL (default http://localhost:8123)
//      PHASE=stock    an existing box before Remoto: onboard and leave a marker, no Remoto checks
//      EXPECT_MARKER=1  fail unless the marker left by PHASE=stock is still there
const HA = process.env.HA_URL || "http://localhost:8123";
const CLIENT_ID = `${HA}/`;
export const ADMIN = { username: "admin", password: "remoto-admin-pass" };
export const CLIENT = { username: "client", password: "remoto-client-pass" };

const post = async (path, body, token, form = false) => {
  const res = await fetch(HA + path, {
    method: "POST",
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
      "Content-Type": form ? "application/x-www-form-urlencoded" : "application/json",
    },
    body: form ? new URLSearchParams(body) : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} → ${res.status} ${await res.text()}`);
  return res.json();
};

// Resolves to the onboarding steps, or null once onboarding is finished
// (the endpoint is then gone and answers 404).
const waitUp = async () => {
  for (let i = 0; i < 90; i++) {
    try {
      const res = await fetch(`${HA}/api/onboarding`);
      if (res.ok) return res.json();
      if (res.status === 404) return null;
    } catch {}
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error("instance did not come up");
};

const ws = (token) =>
  new Promise((resolve, reject) => {
    const sock = new WebSocket(HA.replace(/^http/, "ws") + "/api/websocket");
    let id = 0;
    const waiting = new Map();
    sock.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "auth_required") sock.send(JSON.stringify({ type: "auth", access_token: token }));
      else if (msg.type === "auth_ok")
        resolve({
          call: (payload) =>
            new Promise((res, rej) => {
              const myId = ++id;
              waiting.set(myId, { res, rej });
              sock.send(JSON.stringify({ id: myId, ...payload }));
            }),
          close: () => sock.close(),
        });
      else if (msg.type === "auth_invalid") reject(new Error("ws auth invalid"));
      else if (msg.type === "result") {
        const w = waiting.get(msg.id);
        waiting.delete(msg.id);
        msg.success ? w.res(msg.result) : w.rej(new Error(JSON.stringify(msg.error)));
      }
    };
    sock.onerror = reject;
  });

const STOCK = process.env.PHASE === "stock";
const MARKER = "Existing box marker";

const login = async () => {
  const { flow_id } = await post("/auth/login_flow", {
    client_id: CLIENT_ID,
    handler: ["homeassistant", null],
    redirect_uri: CLIENT_ID,
  });
  const step = await post(`/auth/login_flow/${flow_id}`, { client_id: CLIENT_ID, ...ADMIN });
  if (step.type !== "create_entry") throw new Error(`admin login failed: ${JSON.stringify(step)}`);
  return step.result;
};

const steps = await waitUp();
const onboarded = !steps || steps.find((s) => s.step === "user")?.done;
const auth_code = onboarded
  ? await login()
  : (await post("/api/onboarding/users", { client_id: CLIENT_ID, name: "Admin", ...ADMIN, language: "en" })).auth_code;
const { access_token } = await post(
  "/auth/token",
  { grant_type: "authorization_code", code: auth_code, client_id: CLIENT_ID },
  null,
  true
);
if (!onboarded) {
  await post("/api/onboarding/core_config", {}, access_token);
  await post("/api/onboarding/analytics", {}, access_token);
  await post("/api/onboarding/integration", { client_id: CLIENT_ID, redirect_uri: `${HA}/?auth_callback=1` }, access_token);
}

const conn = await ws(access_token);
const markers = async () => (await conn.call({ type: "input_boolean/list" })).filter((h) => h.name === MARKER);

if (STOCK) {
  if (!(await markers()).length) await conn.call({ type: "input_boolean/create", name: MARKER });
  conn.close();
  console.log("✓ stock box onboarded; marker created");
  process.exit(0);
}

if (process.env.EXPECT_MARKER && !(await markers()).length)
  throw new Error("existing data was lost: the marker created before the install is gone");

// The install enables the integration through configuration.yaml; nothing to click.
const get = async (path) => {
  const res = await fetch(HA + path, { headers: { Authorization: `Bearer ${access_token}` } });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
};
let entries = [];
for (let i = 0; i < 15 && !entries.length; i++) {
  entries = await get("/api/config/config_entries/entry?domain=remoto_branding");
  if (!entries.length) await new Promise((r) => setTimeout(r, 2000));
}
if (entries[0]?.state !== "loaded") throw new Error(`integration not auto-configured: ${JSON.stringify(entries)}`);

const users = await conn.call({ type: "config/auth/list" });
if (!users.some((u) => u.name === "Client")) {
  const { user } = await conn.call({
    type: "config/auth/create",
    name: "Client",
    group_ids: ["system-users"],
    local_only: false,
  });
  await conn.call({
    type: "config/auth_provider/homeassistant/create",
    user_id: user.id,
    ...CLIENT,
  });
}
const themes = await conn.call({ type: "frontend/get_themes" });
if (themes.default_theme !== "Remoto" || !themes.themes.Remoto)
  throw new Error(`Remoto theme not default: ${themes.default_theme}`);
conn.close();
console.log(
  `✓ ${onboarded ? "logged in" : "onboarded"}; integration auto-configured; Remoto theme is default; client user ready` +
    (process.env.EXPECT_MARKER ? "; existing data kept" : "")
);
