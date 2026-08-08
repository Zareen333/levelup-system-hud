/**
 * LevelUp — Solo Leveling System HUD Web Application Architecture
 */

// Initial Seed Quests
const DEFAULT_QUESTS = [
  { id: "Q1", title: "Complete 50 Pushups", xp: 50, category: "Physical", isCompleted: false },
  { id: "Q2", title: "Study Python Data Structures for 1 Hour", xp: 75, category: "Intellect", isCompleted: false },
  { id: "Q3", title: "Build Module 3 of AR Project", xp: 100, category: "Coding", isCompleted: false },
  { id: "Q4", title: "Run 3 Kilometers at High Pace", xp: 120, category: "Physical", isCompleted: false },
  { id: "Q5", title: "Read 20 Pages of Documentation", xp: 80, category: "Intellect", isCompleted: false }
];

// App State Model
class LevelUpApp {
  constructor() {
    this.viewMode = "desktop"; // 'desktop' or 'mobile'
    this.player = {
      name: "Sung Jin-Woo",
      level: 1,
      xp: 0,
      xpToNextLevel: 100,
      stats: { STRENGTH: 10, AGILITY: 10, INTELLIGENCE: 10, AVAILABLE_POINTS: 0 }
    };
    this.quests = [];
    this.speechSynth = window.speechSynthesis || null;
    this.recognition = null;
    this.isListening = false;

    this.init();
  }

  init() {
    this.loadStorage();
    this.bindDOM();
    this.initSpeechRecognition();
    this.render();

    // Check if player registration needed
    const savedName = localStorage.getItem("levelup_player_name");
    if (savedName) {
      this.player.name = savedName;
      document.getElementById("modal-registration").classList.remove("active");
      this.speakAsync(`System online. Welcome back, Hunter ${this.player.name}.`);
    } else {
      document.getElementById("modal-registration").classList.add("active");
    }
  }

  loadStorage() {
    try {
      const storedState = localStorage.getItem("levelup_system_state");
      if (storedState) {
        const parsed = JSON.parse(storedState);
        if (parsed.player) this.player = parsed.player;
        if (parsed.quests && parsed.quests.length > 0) this.quests = parsed.quests;
      }
      if (!this.quests || this.quests.length === 0) {
        this.quests = JSON.parse(JSON.stringify(DEFAULT_QUESTS));
      }
    } catch (err) {
      console.warn("Storage load error:", err);
      this.quests = JSON.parse(JSON.stringify(DEFAULT_QUESTS));
    }
  }

  saveStorage() {
    try {
      localStorage.setItem("levelup_player_name", this.player.name);
      localStorage.setItem("levelup_system_state", JSON.stringify({
        player: this.player,
        quests: this.quests
      }));
    } catch (err) {
      console.error("Storage save error:", err);
    }
  }

  bindDOM() {
    // Buttons
    document.getElementById("btn-mode-toggle").addEventListener("click", () => this.toggleViewMode());
    document.getElementById("btn-add-quest").addEventListener("click", () => this.openAddQuestModal());
    document.getElementById("btn-cancel-quest").addEventListener("click", () => this.closeAddQuestModal());
    document.getElementById("btn-mic-toggle").addEventListener("click", () => this.toggleSpeechRecognition());

    // Forms
    document.getElementById("registration-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const input = document.getElementById("reg-name-input").value.trim();
      if (input) {
        this.player.name = input;
        this.saveStorage();
        document.getElementById("modal-registration").classList.remove("active");
        this.speakAsync(`Welcome, Hunter ${this.player.name}. System HUD online.`);
        this.setFeedback(`Welcome, Hunter ${this.player.name}. Systems operational.`);
        this.render();
      }
    });

    document.getElementById("add-quest-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const title = document.getElementById("add-title").value.trim();
      const xp = parseInt(document.getElementById("add-xp").value, 10) || 50;
      const category = document.getElementById("add-cat").value.trim() || "General";

      if (title) {
        this.addQuest(title, xp, category);
        this.closeAddQuestModal();
      }
    });

    document.getElementById("console-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const inputEl = document.getElementById("console-input");
      const val = inputEl.value;
      inputEl.value = "";
      this.parseTypedCommand(val);
    });

    // Keyboard Shortcuts
    window.addEventListener("keydown", (e) => {
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA")) {
        return; // Don't interrupt typing
      }

      if (e.key >= "1" && e.key <= "9") {
        const idx = parseInt(e.key, 10) - 1;
        this.completeQuestIndex(idx);
      } else if (e.key.toLowerCase() === "l") {
        this.triggerLevelUp();
      } else if (e.key.toLowerCase() === "m") {
        this.toggleViewMode();
      }
    });
  }

  // Voice Output (TTS)
  speakAsync(text) {
    if (!this.speechSynth) return;
    try {
      this.speechSynth.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 0.9;
      this.speechSynth.speak(utterance);
    } catch (err) {
      console.warn("TTS Error:", err);
    }
  }

  // Voice Input (Speech Recognition)
  initSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      document.getElementById("mic-status-text").innerText = "VOICE: NO MIC";
      return;
    }

    try {
      this.recognition = new SpeechRec();
      this.recognition.continuous = true;
      this.recognition.interimResults = false;
      this.recognition.lang = "en-US";

      this.recognition.onresult = (event) => {
        const lastIndex = event.results.length - 1;
        const transcript = event.results[lastIndex][0].transcript.trim().toLowerCase();
        console.log("Voice heard:", transcript);
        this.setFeedback(`VOICE HEARD: "${transcript.toUpperCase()}"`);
        this.parseSpokenIntent(transcript);
      };

      this.recognition.onerror = (event) => {
        console.warn("Speech Rec Error:", event.error);
        if (event.error === "not-allowed") {
          this.isListening = false;
          this.updateMicUI();
        }
      };

      this.recognition.onend = () => {
        if (this.isListening) {
          try { this.recognition.start(); } catch(e){}
        } else {
          this.updateMicUI();
        }
      };
    } catch (err) {
      console.warn("Speech Rec Init Error:", err);
    }
  }

  toggleSpeechRecognition() {
    if (!this.recognition) {
      alert("Web Speech Recognition is not supported in this browser. Try Google Chrome or Edge.");
      return;
    }

    if (this.isListening) {
      this.isListening = false;
      try { this.recognition.stop(); } catch(e){}
      this.updateMicUI();
    } else {
      this.isListening = true;
      try {
        this.recognition.start();
        this.updateMicUI();
      } catch (e) {
        console.warn(e);
      }
    }
  }

  updateMicUI() {
    const btn = document.getElementById("btn-mic-toggle");
    const txt = document.getElementById("mic-status-text");
    if (this.isListening) {
      btn.classList.add("active");
      txt.innerText = "VOICE: LISTENING 🎤";
    } else {
      btn.classList.remove("active");
      txt.innerText = "VOICE: OFF";
    }
  }

  parseSpokenIntent(phrase) {
    if (phrase.includes("level up") || phrase.includes("upgrade level")) {
      this.triggerLevelUp();
      return;
    }

    if (phrase.includes("mobile") || phrase.includes("desktop") || phrase.includes("switch view")) {
      this.toggleViewMode();
      return;
    }

    const numMap = { "1": 0, "one": 0, "first": 0, "2": 1, "two": 1, "second": 1, "3": 2, "three": 2, "third": 2, "4": 3, "four": 3, "fourth": 3, "5": 4, "five": 4, "fifth": 4 };
    for (let [k, idx] of Object.entries(numMap)) {
      if (phrase.includes(`quest ${k}`) || phrase.includes(`complete ${k}`) || phrase.includes(`finish ${k}`)) {
        this.completeQuestIndex(idx);
        return;
      }
    }

    const keywords = ["pushup", "push up", "python", "study", "code", "coding", "run", "read"];
    for (let kw of keywords) {
      if (phrase.includes(kw)) {
        this.completeQuestKeyword(kw);
        return;
      }
    }
  }

  // Domain Logic Methods
  gainXP(amount) {
    if (amount <= 0) return false;
    this.player.xp += amount;
    let leveledUp = false;

    while (this.player.xp >= this.player.xpToNextLevel) {
      this.player.xp -= this.player.xpToNextLevel;
      this.player.level += 1;
      this.player.xpToNextLevel = Math.round(this.player.xpToNextLevel * 1.5);
      this.player.stats.AVAILABLE_POINTS += 3;
      leveledUp = true;
    }

    return leveledUp;
  }

  completeQuestIndex(index) {
    if (index >= 0 && index < this.quests.length) {
      const q = this.quests[index];
      if (!q.isCompleted) {
        q.isCompleted = true;
        const leveledUp = this.gainXP(q.xp);
        this.saveStorage();
        this.speakAsync(`Quest completed: ${q.title}. Granted ${q.xp} experience points.`);

        if (leveledUp) {
          this.showLevelUpModal();
        }

        this.setFeedback(`Completed: '${q.title}' (+${q.xp} XP). Saved.`);
        this.render();
      } else {
        this.setFeedback(`Quest [${index + 1}] is already completed.`, true);
      }
    }
  }

  completeQuestKeyword(keyword) {
    const kw = keyword.toLowerCase();
    const q = this.quests.find(item => !item.isCompleted && (item.title.toLowerCase().includes(kw) || item.category.toLowerCase().includes(kw)));
    if (q) {
      const idx = this.quests.indexOf(q);
      this.completeQuestIndex(idx);
    } else {
      this.setFeedback(`No incomplete quest matching '${keyword}' found.`, true);
    }
  }

  addQuest(title, xp, category) {
    const newQ = {
      id: `Q${this.quests.length + 1}`,
      title: title,
      xp: xp,
      category: category,
      isCompleted: false
    };
    this.quests.push(newQ);
    this.saveStorage();
    this.speakAsync(`New quest added: ${title}.`);
    this.setFeedback(`Added quest: '${title}' (+${xp} XP).`);
    this.render();
  }

  triggerLevelUp() {
    const reqXP = this.player.xpToNextLevel - this.player.xp;
    const leveledUp = this.gainXP(reqXP);
    if (leveledUp) {
      this.saveStorage();
      this.showLevelUpModal();
      this.setFeedback(`Level Up triggered! Player is now Level ${this.player.level}.`);
      this.render();
    }
  }

  showLevelUpModal() {
    const modal = document.getElementById("modal-level-up");
    document.getElementById("levelup-msg").innerText = `PLAYER LEVEL INCREASED TO ${this.player.level}`;
    modal.classList.add("active");
    this.speakAsync(`Warning: Player level increased! Current level is now ${this.player.level}. 3 stat points allocated.`);

    setTimeout(() => {
      modal.classList.remove("active");
    }, 3000);
  }

  toggleViewMode() {
    this.viewMode = this.viewMode === "desktop" ? "mobile" : "desktop";
    document.body.className = `${this.viewMode}-view`;
    const btn = document.getElementById("btn-mode-toggle");
    btn.innerText = this.viewMode === "desktop" ? "📱 MOBILE VIEW" : "💻 DESKTOP VIEW";
    this.setFeedback(`Switched layout to ${this.viewMode.toUpperCase()} mode.`);
  }

  parseTypedCommand(text) {
    let clean = text.trim();
    if (!clean) return;

    if (clean.startsWith("/")) clean = clean.substring(1);
    const parts = clean.split(" ");
    const action = parts[0].toLowerCase();
    const param = parts.slice(1).join(" ");

    if (action === "complete" || action === "finish" || action === "done") {
      if (/^\d+$/.test(param)) {
        this.completeQuestIndex(parseInt(param, 10) - 1);
      } else if (param) {
        this.completeQuestKeyword(param);
      } else {
        this.setFeedback("Specify quest number or title to complete.", true);
      }
    } else if (action === "levelup" || action === "level") {
      this.triggerLevelUp();
    } else if (action === "mode" || action === "toggle" || action === "mobile" || action === "desktop") {
      this.toggleViewMode();
    } else if (action === "addquest" && param) {
      const tokens = param.split("|").map(s => s.trim());
      const title = tokens[0] || "New Quest";
      const xp = parseInt(tokens[1], 10) || 50;
      const cat = tokens[2] || "General";
      this.addQuest(title, xp, cat);
    } else {
      this.completeQuestKeyword(clean);
    }
  }

  setFeedback(msg, isError = false) {
    const el = document.getElementById("console-status");
    el.innerText = `STATUS: ${msg}`;
    el.style.color = isError ? "var(--danger)" : "var(--gold)";
  }

  openAddQuestModal() {
    document.getElementById("add-title").value = "";
    document.getElementById("add-xp").value = "50";
    document.getElementById("add-cat").value = "General";
    document.getElementById("modal-add-quest").classList.add("active");
  }

  closeAddQuestModal() {
    document.getElementById("modal-add-quest").classList.remove("active");
  }

  render() {
    // Header Data
    document.getElementById("player-name").innerText = `PLAYER: ${this.player.name.toUpperCase()}`;
    document.getElementById("level-badge").innerText = `LVL ${this.player.level}`;
    document.getElementById("stat-str").innerText = this.player.stats.STRENGTH;
    document.getElementById("stat-agi").innerText = this.player.stats.AGILITY;
    document.getElementById("stat-int").innerText = this.player.stats.INTELLIGENCE;

    const unspentEl = document.getElementById("unspent-badge");
    if (this.player.stats.AVAILABLE_POINTS > 0) {
      unspentEl.innerText = `[ +${this.player.stats.AVAILABLE_POINTS} STAT POINTS ]`;
      unspentEl.classList.remove("hidden");
    } else {
      unspentEl.classList.add("hidden");
    }

    // XP Bar
    const xpRatio = Math.min(1.0, Math.max(0, this.player.xp / this.player.xpToNextLevel));
    document.getElementById("xp-text").innerText = `XP: ${this.player.xp} / ${this.player.xpToNextLevel} (${Math.round(xpRatio * 100)}%)`;
    document.getElementById("xp-bar-fill").style.width = `${xpRatio * 100}%`;

    // Quest List
    const questListEl = document.getElementById("quest-list");
    questListEl.innerHTML = "";

    this.quests.forEach((q, idx) => {
      const card = document.createElement("div");
      card.className = `quest-card ${q.isCompleted ? 'completed' : ''}`;
      card.innerHTML = `
        <div class="quest-main">
          <span class="quest-key">[${idx + 1}]</span>
          <span class="quest-title">${q.title}</span>
        </div>
        <div class="quest-meta">
          <span class="quest-cat">[${q.category.toUpperCase()}]</span>
          ${q.isCompleted 
            ? '<span class="quest-status-done">✓ COMPLETED</span>' 
            : `<span class="quest-xp">+${q.xp} XP</span>`
          }
        </div>
      `;

      if (!q.isCompleted) {
        card.addEventListener("click", () => this.completeQuestIndex(idx));
      }

      questListEl.appendChild(card);
    });
  }
}

// Instantiate on DOM Load
document.addEventListener("DOMContentLoaded", () => {
  window.app = new LevelUpApp();
});
