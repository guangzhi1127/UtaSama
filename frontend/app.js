const storageKey = "utasama-prototype-state";
const API_BASE_URL = "http://127.0.0.1:8000";
const PET_IDLE_RESET_MS = 9000;

function createDefaultRuntimeConfig() {
  return {
    backendAvailable: false,
    project: "UtaSama",
    entryAgent: "utasama-main",
    agents: [
      {
        id: "utasama-main",
        name: "UtaSama Main Agent",
        domain: "chat、persona-consistency、task-routing、response-merge",
        tag: "主 Agent",
        source: "runtime"
      },
      {
        id: "music-agent",
        name: "Music Agent",
        domain: "music、song、playlist、mood",
        tag: "专项 Agent",
        source: "runtime"
      },
      {
        id: "image-agent",
        name: "Image Agent",
        domain: "draw、image、avatar、pet、sticker",
        tag: "专项 Agent",
        source: "runtime"
      },
      {
        id: "pet-agent",
        name: "Pet Agent",
        domain: "pet、emotion、idle、interaction",
        tag: "专项 Agent",
        source: "runtime"
      }
    ],
    skills: [
      {
        id: "music-player",
        name: "Music Player Skill",
        purpose: "skills/music-player/run",
        tag: "planned",
        source: "runtime"
      },
      {
        id: "image-generation",
        name: "Image Generation Skill",
        purpose: "skills/image-generation/run",
        tag: "planned",
        source: "runtime"
      },
      {
        id: "pet-animation",
        name: "Pet Animation Skill",
        purpose: "skills/pet-animation/run",
        tag: "planned",
        source: "runtime"
      }
    ],
    mcp: [
      {
        id: "music-library",
        name: "Local Music Library MCP",
        capability: "search-track、load-playlist、play-preview",
        tag: "stdio",
        source: "runtime"
      },
      {
        id: "asset-storage",
        name: "Asset Storage MCP",
        capability: "save-asset、list-asset、version-asset",
        tag: "http",
        source: "runtime"
      }
    ]
  };
}

function createDefaultDebugState() {
  return {
    routeAgent: "utasama-main",
    routeLabel: "UtaSama Main Agent",
    intent: "等待消息",
    routeReason: "主聊天 Agent 待机中。",
    historyUsed: 0,
    historyMessageCount: 0,
    summaryUsed: false,
    memoryRecallUsed: false,
    ragUsed: false,
    ragMode: "未检索",
    ragMatchCount: 0,
    ragError: "",
    matchedHints: [],
    preferredSkills: [],
    preferredMcp: [],
    summaryPreview: ""
  };
}

function createDefaultPetState() {
  return {
    mood: "sunny",
    animationState: "idle",
    voiceLine: "我先在这里待机，随时接你话。",
    gesture: "idle-sway",
    followUpHint: "点我一下也行，我会继续陪你待机。"
  };
}

const petMoodFallbackAnimation = {
  sunny: "idle",
  gentle: "idle",
  idol: "sing",
  serious: "think",
  protective: "alert"
};

const petStateManifest = {
  idle: {
    src: "./assets/pet-states/idle.png",
    label: "待机",
    buttonClass: "is-idle",
    moodFallback: "sunny"
  },
  happy: {
    src: "./assets/pet-states/happy.png",
    label: "开心",
    buttonClass: "is-happy",
    moodFallback: "sunny"
  },
  think: {
    src: "./assets/pet-states/think.png",
    label: "思考",
    buttonClass: "is-think",
    moodFallback: "serious"
  },
  sing: {
    src: "./assets/pet-states/sing.png",
    label: "唱歌",
    buttonClass: "is-sing",
    moodFallback: "idol"
  },
  alert: {
    src: "./assets/pet-states/alert.png",
    label: "提醒",
    buttonClass: "is-alert",
    moodFallback: "protective"
  }
};

const petInteractionVoices = {
  idle: [
    {
      mood: "sunny",
      animationState: "happy",
      voiceLine: "戳到我啦，那我先开心一下。",
      gesture: "sparkle-hop",
      followUpHint: "你继续说，我会自己回到待机。"
    },
    {
      mood: "sunny",
      animationState: "idle",
      voiceLine: "我在右下角守着呢，随时都在。",
      gesture: "idle-sway",
      followUpHint: "你继续忙，我会乖乖待机。"
    }
  ],
  happy: [
    {
      mood: "sunny",
      animationState: "happy",
      voiceLine: "好耶，再点一下我也不会介意。",
      gesture: "sparkle-hop",
      followUpHint: "我现在心情很亮。"
    }
  ],
  think: [
    {
      mood: "serious",
      animationState: "think",
      voiceLine: "我在想呢，先别让我丢线索。",
      gesture: "thinking-tilt",
      followUpHint: "你补一句，我就能继续接。"
    }
  ],
  sing: [
    {
      mood: "idol",
      animationState: "sing",
      voiceLine: "哼哼，这里有一点舞台模式。",
      gesture: "note-sway",
      followUpHint: "你继续聊歌，我会跟着进入状态。"
    }
  ],
  alert: [
    {
      mood: "protective",
      animationState: "alert",
      voiceLine: "收到，我还盯着呢。",
      gesture: "alert-burst",
      followUpHint: "需要提醒的时候我会先蹦出来。"
    }
  ]
};

const defaultState = {
  storageVersion: 4,
  activeScene: "companion",
  activeAgent: "utasama-main",
  activeView: "agents",
  sessionId: null,
  petPosition: { x: 32, y: 28 },
  pet: createDefaultPetState(),
  runtimeConfig: createDefaultRuntimeConfig(),
  customRegistries: {
    agents: [],
    skills: [],
    mcp: []
  },
  debug: createDefaultDebugState(),
  messages: []
};

const sceneMap = {
  companion: "日常陪伴",
  music: "音乐共感",
  studio: "灵感画室"
};

const sceneOptions = [
  { id: "companion", label: "日常陪伴" },
  { id: "music", label: "音乐共感" },
  { id: "studio", label: "灵感画室" }
];

const avatarPath = "./assets/uta-avatar.jpg";
const legacyBuiltInIds = {
  agents: new Set(["music-agent", "image-agent", "pet-agent"]),
  skills: new Set(["music-player", "image-generation", "pet-animation"]),
  mcp: new Set(["music-library", "asset-storage"])
};

let petIdleTimerId = null;
let petDragMoved = false;

const state = loadState();

const sceneSwitches = document.getElementById("sceneSwitches");
const agentChips = document.getElementById("agentChips");
const chatFeed = document.getElementById("chatFeed");
const runtimeSummary = document.getElementById("runtimeSummary");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const activeAgentName = document.getElementById("activeAgentName");
const activeSceneName = document.getElementById("activeSceneName");
const petBubble = document.getElementById("petBubble");
const petDock = document.getElementById("petDock");
const petButton = document.getElementById("petButton");
const petImage = document.getElementById("petImage");
const petStatus = document.getElementById("petStatus");
const exportPreview = document.getElementById("exportPreview");

const agentRegistryList = document.getElementById("agentRegistryList");
const skillRegistryList = document.getElementById("skillRegistryList");
const mcpRegistryList = document.getElementById("mcpRegistryList");

const agentForm = document.getElementById("agentForm");
const skillForm = document.getElementById("skillForm");
const mcpForm = document.getElementById("mcpForm");
const copyConfigButton = document.getElementById("copyConfigButton");

initialize();

async function initialize() {
  ensureSessionId();
  bindStaticEvents();
  state.petPosition = clampPetPositionToViewport(state.petPosition);
  applyPetPosition();
  await syncRuntimeConfigFromBackend();
  await syncHistoryFromBackend();
  renderAll();
  if (state.pet.animationState !== "idle") {
    schedulePetIdleReset();
  }
}

function loadState() {
  try {
    const saved = localStorage.getItem(storageKey);
    if (!saved) {
      return structuredClone(defaultState);
    }

    const parsed = JSON.parse(saved);
    const nextState = structuredClone(defaultState);
    nextState.activeScene = sceneMap[parsed.activeScene] ? parsed.activeScene : defaultState.activeScene;
    nextState.activeAgent = typeof parsed.activeAgent === "string" ? parsed.activeAgent : defaultState.activeAgent;
    nextState.activeView = typeof parsed.activeView === "string" ? parsed.activeView : defaultState.activeView;
    nextState.sessionId = typeof parsed.sessionId === "string" ? parsed.sessionId : null;

    if (parsed.petPosition && Number.isFinite(parsed.petPosition.x) && Number.isFinite(parsed.petPosition.y)) {
      nextState.petPosition = parsed.petPosition;
    }

    if (Array.isArray(parsed.messages)) {
      nextState.messages = parsed.messages;
    }

    if (parsed.runtimeConfig) {
      nextState.runtimeConfig = normalizeStoredRuntimeConfig(parsed.runtimeConfig);
    }

    if (parsed.debug) {
      nextState.debug = {
        ...createDefaultDebugState(),
        ...parsed.debug
      };
    }

    nextState.pet = normalizePetState(
      parsed.pet || createPetStateFromLegacyMood(parsed.petMood, parsed.petLine)
    );

    if (parsed.customRegistries) {
      nextState.customRegistries = normalizeStoredCustomRegistries(parsed.customRegistries);
    } else {
      nextState.customRegistries = extractLegacyCustomRegistries(parsed.registries);
    }

    return nextState;
  } catch (error) {
    return structuredClone(defaultState);
  }
}

function normalizeStoredRuntimeConfig(runtimeConfig) {
  const fallback = createDefaultRuntimeConfig();
  return {
    ...fallback,
    ...runtimeConfig,
    agents: Array.isArray(runtimeConfig.agents) ? runtimeConfig.agents : fallback.agents,
    skills: Array.isArray(runtimeConfig.skills) ? runtimeConfig.skills : fallback.skills,
    mcp: Array.isArray(runtimeConfig.mcp) ? runtimeConfig.mcp : fallback.mcp
  };
}

function normalizeStoredCustomRegistries(customRegistries) {
  return {
    agents: Array.isArray(customRegistries.agents) ? customRegistries.agents : [],
    skills: Array.isArray(customRegistries.skills) ? customRegistries.skills : [],
    mcp: Array.isArray(customRegistries.mcp) ? customRegistries.mcp : []
  };
}

function extractLegacyCustomRegistries(registries) {
  if (!registries || typeof registries !== "object") {
    return structuredClone(defaultState.customRegistries);
  }

  return {
    agents: extractLegacyEntries(registries.agents, legacyBuiltInIds.agents, "agents"),
    skills: extractLegacyEntries(registries.skills, legacyBuiltInIds.skills, "skills"),
    mcp: extractLegacyEntries(registries.mcp, legacyBuiltInIds.mcp, "mcp")
  };
}

function extractLegacyEntries(items, builtInIds, kind) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .filter((item) => item && typeof item.id === "string" && !builtInIds.has(item.id))
    .map((item) => normalizeCustomEntry(item, kind));
}

function normalizeCustomEntry(item, kind) {
  if (kind === "agents") {
    return {
      id: item.id,
      name: item.name || item.id,
      domain: item.domain || "待补充职责说明",
      tag: "自定义 Agent",
      source: "custom"
    };
  }

  if (kind === "skills") {
    return {
      id: item.id,
      name: item.name || item.id,
      purpose: item.purpose || "待补充 Skill 说明",
      tag: "自定义 Skill",
      source: "custom"
    };
  }

  return {
    id: item.id,
    name: item.name || item.id,
    capability: item.capability || "待补充 MCP 能力",
    tag: "自定义 MCP",
    source: "custom"
  };
}

function createPetStateFromLegacyMood(mood, voiceLine = "") {
  const fallback = createDefaultPetState();
  const nextMood = typeof mood === "string" && mood ? mood : fallback.mood;
  const animationState = petMoodFallbackAnimation[nextMood] || fallback.animationState;
  return normalizePetState({
    mood: nextMood,
    animationState,
    voiceLine: voiceLine || fallback.voiceLine,
    gesture: fallback.gesture,
    followUpHint: fallback.followUpHint
  });
}

function normalizePetState(petStateLike) {
  const fallback = createDefaultPetState();
  const candidate = petStateLike && typeof petStateLike === "object" ? petStateLike : {};
  const mood = typeof candidate.mood === "string" && candidate.mood ? candidate.mood : fallback.mood;
  const animationState =
    typeof candidate.animationState === "string" && petStateManifest[candidate.animationState]
      ? candidate.animationState
      : petMoodFallbackAnimation[mood] || fallback.animationState;
  const manifest = petStateManifest[animationState];

  return {
    mood: mood || manifest.moodFallback,
    animationState,
    voiceLine:
      typeof candidate.voiceLine === "string" && candidate.voiceLine ? candidate.voiceLine : fallback.voiceLine,
    gesture:
      typeof candidate.gesture === "string" && candidate.gesture ? candidate.gesture : fallback.gesture,
    followUpHint:
      typeof candidate.followUpHint === "string" && candidate.followUpHint
        ? candidate.followUpHint
        : fallback.followUpHint
  };
}

function getPetManifest(animationState) {
  return petStateManifest[animationState] || petStateManifest.idle;
}

function generateSessionId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return `sess_${window.crypto.randomUUID().replaceAll("-", "").slice(0, 12)}`;
  }

  return `sess_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
}

function ensureSessionId() {
  if (!state.sessionId) {
    state.sessionId = generateSessionId();
    saveState();
  }

  return state.sessionId;
}

function setComposerBusy(isBusy) {
  sendButton.disabled = isBusy;
  messageInput.disabled = isBusy;
  sendButton.textContent = isBusy ? "发送中..." : "发送";
}

function clearPetIdleReset() {
  if (!petIdleTimerId) {
    return;
  }
  window.clearTimeout(petIdleTimerId);
  petIdleTimerId = null;
}

function schedulePetIdleReset() {
  clearPetIdleReset();
  if (state.pet.animationState === "idle") {
    return;
  }

  petIdleTimerId = window.setTimeout(() => {
    state.pet = normalizePetState({
      mood: "sunny",
      animationState: "idle",
      voiceLine: "我先回到待机位，有需要再戳我。",
      gesture: "idle-sway",
      followUpHint: "我就在右下角，随时能再动起来。"
    });
    saveState();
    renderAll();
  }, PET_IDLE_RESET_MS);
}

function setPetState(nextPetState, options = {}) {
  state.pet = normalizePetState(nextPetState);

  if (options.save !== false) {
    saveState();
  }

  if (options.render !== false) {
    renderAll();
  } else {
    applyPetState();
  }

  if (options.scheduleIdle) {
    schedulePetIdleReset();
  } else if (options.scheduleIdle === false) {
    clearPetIdleReset();
  }
}

function applyPetState() {
  const petState = normalizePetState(state.pet);
  const manifest = getPetManifest(petState.animationState);

  state.pet = petState;
  petButton.dataset.mood = petState.mood;
  petButton.dataset.animation = petState.animationState;
  petButton.classList.remove("is-idle", "is-happy", "is-think", "is-sing", "is-alert");
  petButton.classList.add(manifest.buttonClass);
  petButton.title = petState.followUpHint;

  if (petImage) {
    petImage.src = manifest.src;
    petImage.alt = `UtaSama pet ${manifest.label}`;
  }

  if (petStatus) {
    petStatus.textContent = `${manifest.label} · ${petState.mood}`;
  }

  if (petBubble) {
    petBubble.textContent = petState.voiceLine;
  }
}

function saveState() {
  localStorage.setItem(storageKey, JSON.stringify(state));
}

function mergeById(baseItems, customItems) {
  const merged = new Map();
  baseItems.concat(customItems).forEach((item) => {
    if (!item || typeof item.id !== "string") {
      return;
    }

    merged.set(item.id, { ...item });
  });
  return Array.from(merged.values());
}

function getMergedRegistries() {
  return {
    agents: mergeById(state.runtimeConfig.agents, state.customRegistries.agents),
    skills: mergeById(state.runtimeConfig.skills, state.customRegistries.skills),
    mcp: mergeById(state.runtimeConfig.mcp, state.customRegistries.mcp)
  };
}

function getAgentItem(agentId) {
  return getMergedRegistries().agents.find((item) => item.id === agentId) || null;
}

function getAgentLabel(agentId) {
  const agent = getAgentItem(agentId);
  return agent ? agent.name : agentId || "UtaSama Main Agent";
}

function ensureActiveAgentExists() {
  const registries = getMergedRegistries();
  if (registries.agents.some((item) => item.id === state.activeAgent)) {
    return;
  }

  state.activeAgent = state.runtimeConfig.entryAgent || "utasama-main";
}

function renderAll() {
  ensureActiveAgentExists();
  renderScenes();
  renderAgentChips();
  renderRuntimeSummary();
  renderMessages();
  renderWorkspaceTabs();
  renderRegistryLists();
  renderExportPreview();
  activeAgentName.textContent = getAgentLabel(state.activeAgent);
  activeSceneName.textContent = sceneMap[state.activeScene];
  applyPetState();
}

function renderScenes() {
  sceneSwitches.innerHTML = "";
  sceneOptions.forEach((scene) => {
    const button = document.createElement("button");
    button.className = `scene-button${scene.id === state.activeScene ? " is-active" : ""}`;
    button.textContent = scene.label;
    button.addEventListener("click", () => {
      state.activeScene = scene.id;
      appendSystemHint(`场景切换到「${scene.label}」`);
      saveState();
      renderAll();
    });
    sceneSwitches.appendChild(button);
  });
}

function renderAgentChips() {
  const registries = getMergedRegistries();
  const entryAgent = state.runtimeConfig.entryAgent;
  const sortedAgents = registries.agents
    .slice()
    .sort((left, right) => {
      if (left.id === entryAgent) {
        return -1;
      }
      if (right.id === entryAgent) {
        return 1;
      }
      return left.name.localeCompare(right.name, "zh-CN");
    });

  agentChips.innerHTML = "";
  sortedAgents.forEach((agent) => {
    const button = document.createElement("button");
    button.className = `agent-chip${agent.id === state.activeAgent ? " is-active" : ""}`;
    button.textContent = agent.name;
    button.addEventListener("click", () => {
      state.activeAgent = agent.id;
      saveState();
      renderAll();
      petBubble.textContent = `${agent.name} 已经就位，我会跟着当前模式一起切换。`;
    });
    agentChips.appendChild(button);
  });
}

function formatBooleanFlag(value) {
  return value ? "已使用" : "未使用";
}

function formatListValue(items, empty = "暂无") {
  if (!Array.isArray(items) || items.length === 0) {
    return empty;
  }
  return items.join(" / ");
}

function renderRuntimeSummary() {
  const registries = getMergedRegistries();
  const rows = [
    ["主会话", getAgentLabel(state.runtimeConfig.entryAgent)],
    ["场景", sceneMap[state.activeScene]],
    ["会话", state.sessionId || "待创建"],
    ["当前路由", state.debug.routeLabel || getAgentLabel(state.debug.routeAgent)],
    ["意图", state.debug.intent],
    ["路由原因", state.debug.routeReason],
    ["历史", `${state.debug.historyUsed} / ${state.debug.historyMessageCount}`],
    ["摘要", formatBooleanFlag(state.debug.summaryUsed)],
    ["记忆召回", formatBooleanFlag(state.debug.memoryRecallUsed)],
    ["知识库", formatBooleanFlag(state.debug.ragUsed)],
    ["RAG模式", `${state.debug.ragMode} / ${state.debug.ragMatchCount}`],
    ["建议 Skills", formatListValue(state.debug.preferredSkills)],
    ["建议 MCP", formatListValue(state.debug.preferredMcp)],
    ["桌宠", `${getPetManifest(state.pet.animationState).label} / ${state.pet.mood}`],
    ["Skills", `${registries.skills.length} 项`],
    ["MCP", `${registries.mcp.length} 项`]
  ];

  runtimeSummary.innerHTML = rows
    .map(([label, value]) => `<li><strong>${escapeHtml(label)}</strong><span>${escapeHtml(String(value))}</span></li>`)
    .join("");
}

function renderMessages() {
  chatFeed.innerHTML = "";

  if (state.messages.length === 0) {
    const row = document.createElement("article");
    row.className = "message-row is-agent";
    row.appendChild(buildAvatar());

    const body = document.createElement("div");
    body.className = "message-body";
    body.innerHTML = `
      <div class="message-meta">
        <span>${escapeHtml(getAgentLabel(state.runtimeConfig.entryAgent))}</span>
        <span>现在</span>
      </div>
      <div class="message-bubble">新的会话已经准备好了。接下来真正发出的消息会进入这条会话历史，后端也会按这条线继续记。</div>
    `;
    row.appendChild(body);
    chatFeed.appendChild(row);
  }

  state.messages.forEach((message) => {
    const row = document.createElement("article");
    row.className = `message-row ${message.role === "user" ? "is-user" : "is-agent"}`;

    if (message.role === "agent") {
      row.appendChild(buildAvatar());
    }

    const body = document.createElement("div");
    body.className = "message-body";
    body.innerHTML = `
      <div class="message-meta">
        <span>${escapeHtml(message.agent)}</span>
        <span>${escapeHtml(message.time)}</span>
      </div>
      <div class="message-bubble">${escapeHtml(message.text)}</div>
    `;
    row.appendChild(body);

    if (message.role === "user") {
      row.appendChild(buildAvatar("你"));
    }

    chatFeed.appendChild(row);
  });

  chatFeed.scrollTop = chatFeed.scrollHeight;
}

function formatHistoryTime(value) {
  if (!value) {
    return currentTime();
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return currentTime();
  }

  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit"
  });
}

function mapHistoryRecordToMessage(record) {
  const isAssistant = record.role === "assistant";
  const agentId = record.agent_id || state.runtimeConfig.entryAgent;

  return {
    role: isAssistant ? "agent" : "user",
    agent: isAssistant ? getAgentLabel(agentId) : "你",
    time: formatHistoryTime(record.created_at),
    text: record.content || ""
  };
}

function normalizeRuntimeConfig(data) {
  return {
    backendAvailable: true,
    project: data.project || "UtaSama",
    entryAgent: data.entry_agent || "utasama-main",
    agents: Array.isArray(data.agents)
      ? data.agents.map((agent) => ({
          id: agent.id,
          name: agent.display_name || agent.id,
          domain: agent.summary || "待补充职责说明",
          tag: agent.type === "primary" ? "主 Agent" : "专项 Agent",
          source: "runtime"
        }))
      : [],
    skills: Array.isArray(data.skills)
      ? data.skills.map((skill) => ({
          id: skill.id,
          name: skill.display_name || skill.id,
          purpose: skill.summary || "待补充 Skill 说明",
          tag: skill.status || skill.category || "planned",
          source: "runtime"
        }))
      : [],
    mcp: Array.isArray(data.mcp)
      ? data.mcp.map((provider) => ({
          id: provider.id,
          name: provider.display_name || provider.id,
          capability: provider.summary || "待补充 MCP 能力",
          tag: provider.transport || "unknown",
          source: "runtime"
        }))
      : []
  };
}

async function syncRuntimeConfigFromBackend() {
  try {
    const response = await fetch(`${API_BASE_URL}/runtime/config`);
    if (!response.ok) {
      throw new Error(`Runtime config request failed: ${response.status}`);
    }

    const data = await response.json();
    state.runtimeConfig = normalizeRuntimeConfig(data);
    state.debug.routeAgent = state.debug.routeAgent || state.runtimeConfig.entryAgent;
    state.debug.routeLabel = getAgentLabel(state.debug.routeAgent);
    ensureActiveAgentExists();
    saveState();
  } catch (error) {
    state.runtimeConfig.backendAvailable = false;
  }
}

async function syncHistoryFromBackend() {
  const sessionId = ensureSessionId();

  try {
    const response = await fetch(`${API_BASE_URL}/history/${encodeURIComponent(sessionId)}?limit=200`);
    if (!response.ok) {
      return;
    }

    const data = await response.json();
    state.debug.historyMessageCount = Number.isFinite(data.message_count) ? data.message_count : 0;
    state.debug.summaryUsed = Boolean(data.summary);

    if (!Array.isArray(data.recent_messages) || data.recent_messages.length === 0) {
      saveState();
      return;
    }

    state.messages = data.recent_messages.map(mapHistoryRecordToMessage);
    saveState();
  } catch (error) {
    // Keep the local UI usable even if hydration fails.
  }
}

function buildAvatar(label = "U") {
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";

  if (label === "你") {
    avatar.innerHTML = `<div style="width:100%;height:100%;display:grid;place-items:center;background:#24323a;color:#edf4f3;font-weight:700;">你</div>`;
  } else {
    avatar.innerHTML = `<img src="${avatarPath}" alt="avatar" />`;
  }

  return avatar;
}

function renderWorkspaceTabs() {
  document.querySelectorAll(".workspace-tab").forEach((button) => {
    const isActive = button.dataset.view === state.activeView;
    button.classList.toggle("is-active", isActive);
  });

  document.querySelectorAll(".workspace-view").forEach((view) => {
    const isActive = view.dataset.view === state.activeView;
    view.classList.toggle("is-active", isActive);
  });
}

function renderRegistryLists() {
  const registries = getMergedRegistries();

  renderResourceList(
    agentRegistryList,
    registries.agents,
    (item) => item.name,
    (item) => item.domain,
    (item) => item.tag || "专项分工"
  );
  renderResourceList(
    skillRegistryList,
    registries.skills,
    (item) => item.name,
    (item) => item.purpose,
    (item) => item.tag || "待接入"
  );
  renderResourceList(
    mcpRegistryList,
    registries.mcp,
    (item) => item.name,
    (item) => item.capability,
    (item) => item.tag || "预留接口"
  );
}

function renderResourceList(target, items, titleGetter, subGetter, tagGetter) {
  target.innerHTML = "";
  items.forEach((item) => {
    const tagText = typeof tagGetter === "function" ? tagGetter(item) : tagGetter;
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="resource-main">
        <strong>${escapeHtml(titleGetter(item))}</strong>
        <span class="resource-tag">${escapeHtml(tagText)}</span>
      </div>
      <div class="resource-sub">${escapeHtml(subGetter(item))}</div>
    `;
    target.appendChild(li);
  });
}

function renderExportPreview() {
  exportPreview.textContent = JSON.stringify(
    {
      sessionId: state.sessionId,
      activeScene: state.activeScene,
      activeAgent: state.activeAgent,
      pet: state.pet,
      runtimeConfig: state.runtimeConfig,
      customRegistries: state.customRegistries,
      debug: state.debug
    },
    null,
    2
  );
}

function bindStaticEvents() {
  document.querySelectorAll(".workspace-tab").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeView = button.dataset.view;
      saveState();
      renderWorkspaceTabs();
    });
  });

  document.querySelectorAll("[data-prefill]").forEach((button) => {
    button.addEventListener("click", () => {
      messageInput.value = button.dataset.prefill;
      messageInput.focus();
    });
  });

  sendButton.addEventListener("click", submitMessage);
  messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submitMessage();
    }
  });

  agentForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(agentForm);
    const name = formData.get("name").toString().trim();
    const domain = formData.get("domain").toString().trim();
    if (!name || !domain) {
      return;
    }

    state.customRegistries.agents.push({
      id: ensureUniqueId(getMergedRegistries().agents, slugify(name)),
      name,
      domain,
      tag: "自定义 Agent",
      source: "custom"
    });
    agentForm.reset();
    saveState();
    renderAll();
  });

  skillForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(skillForm);
    const name = formData.get("name").toString().trim();
    const purpose = formData.get("purpose").toString().trim();
    if (!name || !purpose) {
      return;
    }

    state.customRegistries.skills.push({
      id: ensureUniqueId(getMergedRegistries().skills, slugify(name)),
      name,
      purpose,
      tag: "自定义 Skill",
      source: "custom"
    });
    skillForm.reset();
    saveState();
    renderAll();
  });

  mcpForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(mcpForm);
    const name = formData.get("name").toString().trim();
    const capability = formData.get("capability").toString().trim();
    if (!name || !capability) {
      return;
    }

    state.customRegistries.mcp.push({
      id: ensureUniqueId(getMergedRegistries().mcp, slugify(name)),
      name,
      capability,
      tag: "自定义 MCP",
      source: "custom"
    });
    mcpForm.reset();
    saveState();
    renderAll();
  });

  copyConfigButton.addEventListener("click", async () => {
    const copied = await copyText(exportPreview.textContent);
    petBubble.textContent = copied
      ? "当前配置已经复制好了，后面可以直接拿去接真实运行时。"
      : "剪贴板权限没放行，不过导出 JSON 还在右侧，你可以直接取用。";
  });

  petButton.addEventListener("click", handlePetClick);

  enablePetDrag();
}

function ensureUniqueId(items, baseId) {
  const seed = baseId || `custom-${Date.now().toString(36)}`;
  const usedIds = new Set(items.map((item) => item.id));
  if (!usedIds.has(seed)) {
    return seed;
  }

  let suffix = 2;
  while (usedIds.has(`${seed}-${suffix}`)) {
    suffix += 1;
  }
  return `${seed}-${suffix}`;
}

function handlePetClick() {
  if (petDragMoved) {
    petDragMoved = false;
    return;
  }

  const currentAnimation = state.pet.animationState;
  const options = petInteractionVoices[currentAnimation] || petInteractionVoices.idle;
  const next = options[Math.floor(Math.random() * options.length)];
  setPetState(next, { save: true, render: true, scheduleIdle: true });
}

function syncSceneWithAgent(agentId) {
  if (agentId === "music-agent") {
    state.activeScene = "music";
    return;
  }

  if (agentId === "image-agent") {
    state.activeScene = "studio";
    return;
  }

  if (agentId === state.runtimeConfig.entryAgent || agentId === "pet-agent") {
    state.activeScene = "companion";
  }
}

function updatePetStateFromResponse(data) {
  const backendPetState =
    data && data.pet_state && typeof data.pet_state === "object"
      ? data.pet_state
      : createPetStateFromLegacyMood(data.pet_mood, data.pet_line);
  state.pet = normalizePetState(backendPetState);
}

function updateDebugStateFromResponse(data) {
  state.debug.routeAgent = data.active_agent || state.runtimeConfig.entryAgent;
  state.debug.routeLabel = data.agent_display_name || getAgentLabel(state.debug.routeAgent);
  state.debug.intent = data.intent || "companion-chat";
  state.debug.routeReason = data.route_reason || "未返回路由原因。";
  state.debug.historyUsed = Number.isFinite(data.history_used) ? data.history_used : 0;
  state.debug.historyMessageCount = Number.isFinite(data.history_message_count) ? data.history_message_count : 0;
  state.debug.summaryUsed = Boolean(data.summary_used);
  state.debug.memoryRecallUsed = Boolean(data.memory_recall_used);
  state.debug.ragUsed = Boolean(data.rag_used);
  state.debug.ragMode = data.rag_mode || "未知";
  state.debug.ragMatchCount = Number.isFinite(data.rag_match_count) ? data.rag_match_count : 0;
  state.debug.ragError = data.rag_error || "";
  state.debug.matchedHints = Array.isArray(data.matched_hints) ? data.matched_hints : [];
  state.debug.preferredSkills = Array.isArray(data.preferred_skills) ? data.preferred_skills : [];
  state.debug.preferredMcp = Array.isArray(data.preferred_mcp) ? data.preferred_mcp : [];
  state.debug.summaryPreview = data.summary_preview || "";
}

async function submitMessage() {
  const text = messageInput.value.trim();
  if (!text) {
    return;
  }

  const sessionId = ensureSessionId();

  state.messages.push({
    role: "user",
    agent: "你",
    time: currentTime(),
    text
  });

  messageInput.value = "";
  saveState();
  renderAll();
  setComposerBusy(true);

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: text,
        session_id: sessionId
      })
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }

    const data = await response.json();
    state.sessionId = data.session_id || state.sessionId;
    updateDebugStateFromResponse(data);
    updatePetStateFromResponse(data);

    const activeAgentId = data.active_agent || state.activeAgent;
    state.activeAgent = activeAgentId;
    syncSceneWithAgent(activeAgentId);

    state.messages.push({
      role: "agent",
      agent: data.agent_display_name || getAgentLabel(activeAgentId),
      time: currentTime(),
      text: data.reply_text || "我刚刚接住了你的话，但这次回复内容是空的。"
    });

    saveState();
    renderAll();
    schedulePetIdleReset();
  } catch (error) {
    state.messages.push({
      role: "agent",
      agent: "System",
      time: currentTime(),
      text: "后端暂时没有连上，或者接口请求失败了。你先检查 FastAPI 服务是不是还开着。"
    });

    state.pet = normalizePetState({
      mood: "protective",
      animationState: "alert",
      voiceLine: "我这边没接到后端回话，先帮你盯着服务状态。",
      gesture: "alert-burst",
      followUpHint: "等服务恢复，我会继续接住你的消息。"
    });

    saveState();
    renderAll();
    schedulePetIdleReset();
  } finally {
    setComposerBusy(false);
    messageInput.focus();
  }
}

function appendSystemHint(text) {
  state.messages.push({
    role: "agent",
    agent: getAgentLabel(state.runtimeConfig.entryAgent),
    time: currentTime(),
    text
  });
}

function currentTime() {
  return new Date().toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit"
  });
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

async function copyText(value) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch (error) {
    // Fall through to the legacy copy path.
  }

  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();

  let copied = false;

  try {
    copied = document.execCommand("copy");
  } catch (error) {
    copied = false;
  }

  textarea.remove();
  return copied;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function applyPetPosition() {
  document.documentElement.style.setProperty("--pet-x", `${state.petPosition.x}px`);
  document.documentElement.style.setProperty("--pet-y", `${state.petPosition.y}px`);
}

function clampPetPositionToViewport(position) {
  const fallback = defaultState.petPosition;
  const candidate =
    position && Number.isFinite(position.x) && Number.isFinite(position.y) ? position : fallback;
  const dockWidth = petDock?.offsetWidth || 240;
  const dockHeight = petDock?.offsetHeight || 260;
  const maxX = Math.max(12, window.innerWidth - dockWidth - 12);
  const maxY = Math.max(12, window.innerHeight - dockHeight - 12);

  return {
    x: Math.min(maxX, Math.max(12, candidate.x)),
    y: Math.min(maxY, Math.max(12, candidate.y))
  };
}

function enablePetDrag() {
  let pointerArmed = false;
  let dragStarted = false;
  let activePointerId = null;
  let startClientX = 0;
  let startClientY = 0;
  let startPetPosition = { ...state.petPosition };

  function resetPointerState(savePosition) {
    if (activePointerId !== null && petButton.hasPointerCapture?.(activePointerId)) {
      try {
        petButton.releasePointerCapture(activePointerId);
      } catch (error) {
        // Ignore release failures and just reset the local drag state.
      }
    }

    pointerArmed = false;
    dragStarted = false;
    activePointerId = null;
    petButton.dataset.dragging = "false";

    if (savePosition) {
      saveState();
    }
  }

  petButton.addEventListener("pointerdown", (event) => {
    if (!event.isPrimary) {
      return;
    }

    pointerArmed = true;
    dragStarted = false;
    petDragMoved = false;
    activePointerId = event.pointerId;
    startClientX = event.clientX;
    startClientY = event.clientY;
    startPetPosition = { ...state.petPosition };
    petButton.dataset.dragging = "false";
    petButton.setPointerCapture(event.pointerId);
  });

  petButton.addEventListener("pointermove", (event) => {
    if (!pointerArmed || event.pointerId !== activePointerId) {
      return;
    }

    if (typeof event.buttons === "number" && event.buttons === 0) {
      resetPointerState(dragStarted);
      return;
    }

    const deltaX = startClientX - event.clientX;
    const deltaY = startClientY - event.clientY;

    if (!dragStarted) {
      if (Math.hypot(deltaX, deltaY) < 8) {
        return;
      }

      dragStarted = true;
      petDragMoved = true;
      petButton.dataset.dragging = "true";
    }

    state.petPosition = clampPetPositionToViewport({
      x: startPetPosition.x + deltaX,
      y: startPetPosition.y + deltaY
    });
    applyPetPosition();
  });

  petButton.addEventListener("pointerup", (event) => {
    if (!pointerArmed || event.pointerId !== activePointerId) {
      return;
    }

    resetPointerState(dragStarted);
  });

  petButton.addEventListener("pointercancel", () => {
    resetPointerState(false);
  });

  petButton.addEventListener("lostpointercapture", () => {
    resetPointerState(dragStarted);
  });

  window.addEventListener("resize", () => {
    state.petPosition = clampPetPositionToViewport(state.petPosition);
    applyPetPosition();
    saveState();
  });
}
