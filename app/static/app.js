const state = {
  apiToken: localStorage.getItem("apiToken"),
  email: localStorage.getItem("email"),
};

const authSection = document.getElementById("auth-section");
const dashboardSection = document.getElementById("dashboard-section");
const sessionStatus = document.getElementById("session-status");
const authMessage = document.getElementById("auth-message");
const createMessage = document.getElementById("create-message");
const linksBody = document.getElementById("links-body");
const analyticsPanel = document.getElementById("analytics-panel");
const analyticsOutput = document.getElementById("analytics-output");

async function apiRequest(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && state.apiToken) {
    headers["Authorization"] = `Bearer ${state.apiToken}`;
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed with status ${response.status}`);
  }
  return payload;
}

function setSession(email, apiToken) {
  state.email = email;
  state.apiToken = apiToken;
  localStorage.setItem("email", email);
  localStorage.setItem("apiToken", apiToken);
  render();
}

function clearSession() {
  state.email = null;
  state.apiToken = null;
  localStorage.removeItem("email");
  localStorage.removeItem("apiToken");
  render();
}

function render() {
  const signedIn = Boolean(state.apiToken);
  authSection.hidden = signedIn;
  dashboardSection.hidden = !signedIn;
  sessionStatus.textContent = signedIn ? `Signed in as ${state.email}` : "Not signed in";
  if (signedIn) {
    loadLinks();
  }
}

async function loadLinks() {
  try {
    const links = await apiRequest("/api/links");
    linksBody.innerHTML = "";
    for (const link of links) {
      linksBody.appendChild(renderLinkRow(link));
    }
  } catch (err) {
    createMessage.textContent = err.message;
  }
}

function renderLinkRow(link) {
  const row = document.createElement("tr");

  const shortUrlCell = document.createElement("td");
  const anchor = document.createElement("a");
  anchor.href = link.short_url;
  anchor.textContent = link.short_url;
  anchor.target = "_blank";
  shortUrlCell.appendChild(anchor);

  const destinationCell = document.createElement("td");
  destinationCell.textContent = link.long_url;

  const clicksCell = document.createElement("td");
  clicksCell.textContent = link.click_count;

  const statusCell = document.createElement("td");
  statusCell.textContent = link.is_active ? "active" : "inactive";

  const actionsCell = document.createElement("td");
  const analyticsButton = document.createElement("button");
  analyticsButton.textContent = "Analytics";
  analyticsButton.addEventListener("click", () => showAnalytics(link.id));
  actionsCell.appendChild(analyticsButton);

  row.append(shortUrlCell, destinationCell, clicksCell, statusCell, actionsCell);
  return row;
}

async function showAnalytics(linkId) {
  try {
    const analytics = await apiRequest(`/api/links/${linkId}/analytics`);
    analyticsPanel.hidden = false;
    analyticsOutput.textContent = JSON.stringify(analytics, null, 2);
  } catch (err) {
    analyticsPanel.hidden = false;
    analyticsOutput.textContent = err.message;
  }
}

document.getElementById("auth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  authMessage.textContent = "";

  const action = event.submitter.dataset.action;
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    const path = action === "register" ? "/api/auth/register" : "/api/auth/login";
    const result = await apiRequest(path, { method: "POST", body: { email, password }, auth: false });
    setSession(result.email, result.api_token);
  } catch (err) {
    authMessage.textContent = err.message;
  }
});

document.getElementById("create-link-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  createMessage.textContent = "";

  const longUrl = document.getElementById("long-url").value;
  const customCode = document.getElementById("custom-code").value || undefined;

  try {
    await apiRequest("/api/links", { method: "POST", body: { long_url: longUrl, custom_code: customCode } });
    event.target.reset();
    loadLinks();
  } catch (err) {
    createMessage.textContent = err.message;
  }
});

render();
