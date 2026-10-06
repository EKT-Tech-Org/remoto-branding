// Onboards a fresh instance, adds Remoto Branding, and creates a non-admin client user.
// Env: HA_URL (default http://localhost:8123)
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

const waitUp = async () => {
  for (let i = 0; i < 90; i++) {
    try {
      if ((await fetch(`${HA}/api/onboarding`)).ok) return;
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

await waitUp();
const { auth_code } = await post("/api/onboarding/users", {
  client_id: CLIENT_ID,
  name: "Admin",
  ...ADMIN,
  language: "en",
});
const { access_token } = await post(
  "/auth/token",
  { grant_type: "authorization_code", code: auth_code, client_id: CLIENT_ID },
  null,
  true
);
await post("/api/onboarding/core_config", {}, access_token);
await post("/api/onboarding/analytics", {}, access_token);
await post("/api/onboarding/integration", { client_id: CLIENT_ID, redirect_uri: `${HA}/?auth_callback=1` }, access_token);

const flow = await post("/api/config/config_entries/flow", { handler: "remoto_branding" }, access_token);
const entry = await post(
  `/api/config/config_entries/flow/${flow.flow_id}`,
  { brand_name: "Remoto", primary_color: "#553D9F" },
  access_token
);
if (entry.type !== "create_entry") throw new Error(`config flow: ${JSON.stringify(entry)}`);

const conn = await ws(access_token);
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
conn.close();
console.log("✓ onboarded, Remoto Branding added, non-admin user 'client' created");
