"""
patch_frontend.py
Replaces the <script> block in the ResQmeal HTML with the backend-integrated version.
"""

import os

SRC = r"f:\ResQmeal-1\frontend\index ResQmeal - updated auth.html"

NEW_SCRIPT = r"""  <script>
    const ngos = [
      { name: "Hope Shelter", distance: 1.8, need: 110, vehicle: "van", storage: "serve now", verified: true },
      { name: "Anbu Old Age Home", distance: 2.6, need: 70, vehicle: "auto", storage: "hot meals", verified: true },
      { name: "Little Hands Home", distance: 4.3, need: 95, vehicle: "bike + car", storage: "sealed only", verified: true }
    ];

    const donors = [
      { name: "Green Leaf Restaurant", distance: 1.4, avg: 38, today: 44, urgency: 72 },
      { name: "Sri Devi Wedding Hall", distance: 2.1, avg: 130, today: 150, urgency: 94 },
      { name: "City Hostel Mess", distance: 3.2, avg: 55, today: 49, urgency: 64 },
      { name: "FreshMart Supermarket", distance: 4.7, avg: 28, today: 32, urgency: 48 }
    ];

    const routeStops = [
      ["Sri Devi Wedding Hall", "120 meals", "Pickup 7:25 PM"],
      ["Green Leaf Restaurant", "44 meals", "Pickup 7:45 PM"],
      ["Hope Shelter", "Delivery", "Arrive 8:05 PM"]
    ];

    const days = [
      ["Mon", 22], ["Tue", 28], ["Wed", 31], ["Thu", 26], ["Fri", 52], ["Sat", 46], ["Sun", 35]
    ];

    const leaders = [
      ["Sri Devi Wedding Hall", "2,940 meals rescued"],
      ["Green Leaf Restaurant", "1,880 meals rescued"],
      ["Volunteer Kavya", "126 completed pickups"],
      ["City Hostel Mess", "1,105 meals rescued"]
    ];

    const USER_STORAGE_KEY = "resqmealUsers";
    const SESSION_STORAGE_KEY = "resqmealCurrentUser";
    let currentUser = null;
    let pendingSignup = null;
    let pendingOtp = "";

    /* ── Backend integration ─────────────────────────────────────────────── */
    const API_BASE = "http://localhost:5000";

    async function apiCall(path, options = {}) {
      const token = sessionStorage.getItem("resqmealToken");
      const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(API_BASE + path, { ...options, headers });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Request failed");
      return data;
    }

    async function backendAvailable() {
      try {
        const res = await fetch(API_BASE + "/api/health", { signal: AbortSignal.timeout(1500) });
        return res.ok;
      } catch { return false; }
    }
    /* ──────────────────────────────────────────────────────────────────────── */

    const authScreen = document.getElementById("authScreen");
    const appShell = document.getElementById("appShell");
    const loginView = document.getElementById("loginView");
    const signupView = document.getElementById("signupView");
    const loginUserType = document.getElementById("loginUserType");
    const loginUsername = document.getElementById("loginUsername");
    const loginPassword = document.getElementById("loginPassword");
    const loginError = document.getElementById("loginError");
    const signupError = document.getElementById("signupError");
    const signupSuccess = document.getElementById("signupSuccess");
    const otpBox = document.getElementById("otpBox");
    const profileBtn = document.getElementById("profileBtn");
    const profilePanel = document.getElementById("profilePanel");
    const aiChatPanel = document.getElementById("aiChatPanel");
    const aiChatLog = document.getElementById("aiChatLog");
    const aiChatInput = document.getElementById("aiChatInput");

    const tabs = document.querySelectorAll(".tab");
    const navButtons = document.querySelectorAll(".nav-btn");
    const pageTitle = document.getElementById("pageTitle");
    const liveStatus = document.getElementById("liveStatus");

    navButtons.forEach(button => {
      button.addEventListener("click", () => { showTab(button.dataset.tab); });
    });

    document.getElementById("loginBtn").addEventListener("click", login);
    document.getElementById("showSignupBtn").addEventListener("click", () => showAuthView("signup"));
    document.getElementById("showLoginBtn").addEventListener("click", () => showAuthView("login"));
    document.getElementById("sendOtpBtn").addEventListener("click", sendOtp);
    document.getElementById("verifyOtpBtn").addEventListener("click", verifyOtpAndCreateAccount);
    document.getElementById("logoutBtn").addEventListener("click", logout);
    loginPassword.addEventListener("keydown", e => { if (e.key === "Enter") login(); });
    document.getElementById("otpInput").addEventListener("keydown", e => { if (e.key === "Enter") verifyOtpAndCreateAccount(); });
    document.getElementById("aiChatToggle").addEventListener("click", openAiChat);
    document.getElementById("aiChatClose").addEventListener("click", () => aiChatPanel.classList.add("hidden"));
    document.getElementById("aiChatForm").addEventListener("submit", handleAiQuestion);
    profileBtn.addEventListener("click", () => profilePanel.classList.toggle("hidden"));
    document.addEventListener("click", event => {
      if (!profilePanel.contains(event.target) && event.target !== profileBtn) profilePanel.classList.add("hidden");
    });

    function initials(name) {
      return name.split(/\s+/).filter(Boolean).slice(0, 2).map(p => p[0].toUpperCase()).join("") || "FR";
    }

    /* ── Local storage helpers (fallback when backend is offline) ──────────── */
    function getUsers() {
      try { return JSON.parse(localStorage.getItem(USER_STORAGE_KEY)) || []; } catch { return []; }
    }
    function saveUsers(users) { localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(users)); }
    function normalizeUsername(u) { return u.trim().toLowerCase(); }
    function roleLabel(role) { return role === "ngo" ? "NGO" : "Food Donor"; }

    function showAuthView(view) {
      loginError.textContent = "";
      signupError.textContent = "";
      signupSuccess.textContent = "";
      loginView.classList.toggle("hidden", view !== "login");
      signupView.classList.toggle("hidden", view !== "signup");
      location.hash = view;
    }

    function validateSignupLocal() {
      const account = {
        fullName: document.getElementById("signupFullName").value.trim(),
        username: document.getElementById("signupUsername").value.trim(),
        phone: document.getElementById("signupPhone").value.trim(),
        email: document.getElementById("signupEmail").value.trim(),
        password: document.getElementById("signupPassword").value,
        confirmPassword: document.getElementById("signupConfirmPassword").value,
        role: document.getElementById("signupUserType").value
      };
      if (!account.fullName || !account.username || !account.phone || !account.email || !account.password || !account.confirmPassword)
        return { error: "Please fill in every sign up field." };
      if (!/^\S+@\S+\.\S+$/.test(account.email)) return { error: "Please enter a valid email address." };
      if (!/^\+?[0-9\s-]{8,15}$/.test(account.phone)) return { error: "Please enter a valid phone number." };
      if (account.password.length < 6) return { error: "Password must be at least 6 characters." };
      if (account.password !== account.confirmPassword) return { error: "Password and confirm password do not match." };
      return { account };
    }

    /* ── Send OTP ──────────────────────────────────────────────────────────── */
    async function sendOtp() {
      signupError.textContent = "";
      signupSuccess.textContent = "";
      const localResult = validateSignupLocal();
      if (localResult.error) { signupError.textContent = localResult.error; otpBox.classList.add("hidden"); return; }
      const account = localResult.account;

      if (await backendAvailable()) {
        try {
          const res = await apiCall("/api/auth/send-otp", {
            method: "POST",
            body: JSON.stringify({ full_name: account.fullName, username: account.username, phone: account.phone, email: account.email, password: account.password, role: account.role }),
          });
          pendingSignup = account; pendingOtp = null;
          otpBox.classList.remove("hidden");
          document.getElementById("otpInput").value = "";
          signupSuccess.textContent = res.otp_code
            ? `OTP sent to ${account.phone}. (Dev mode – use: ${res.otp_code})`
            : `OTP sent to ${account.phone}.`;
          return;
        } catch (err) { signupError.textContent = err.message; return; }
      }
      // Offline fallback
      const users = getUsers();
      if (users.some(u => normalizeUsername(u.username) === normalizeUsername(account.username))) { signupError.textContent = "That username is already registered."; return; }
      if (users.some(u => u.phone === account.phone)) { signupError.textContent = "That phone number is already registered."; return; }
      pendingSignup = account;
      pendingOtp = String(Math.floor(100000 + Math.random() * 900000));
      otpBox.classList.remove("hidden");
      document.getElementById("otpInput").value = "";
      signupSuccess.textContent = `OTP sent to ${account.phone}. (Offline demo – use: ${pendingOtp})`;
    }

    /* ── Verify OTP and Create Account ──────────────────────────────────────── */
    async function verifyOtpAndCreateAccount() {
      signupError.textContent = "";
      const enteredOtp = document.getElementById("otpInput").value.trim();
      if (!pendingSignup) { signupError.textContent = "Please send OTP first."; return; }

      if (await backendAvailable()) {
        try {
          const res = await apiCall("/api/auth/verify-otp", {
            method: "POST",
            body: JSON.stringify({ full_name: pendingSignup.fullName, username: pendingSignup.username, phone: pendingSignup.phone, email: pendingSignup.email, password: pendingSignup.password, role: pendingSignup.role, otp_code: enteredOtp }),
          });
          sessionStorage.setItem("resqmealToken", res.token);
          currentUser = { fullName: res.user.full_name, username: res.user.username, phone: res.user.phone, email: res.user.email, role: res.user.role, verified: true };
          signupSuccess.textContent = "Account created successfully. Logging you in…";
          setTimeout(enterDashboard, 900);
          return;
        } catch (err) { signupError.textContent = err.message; return; }
      }
      // Offline fallback
      if (!pendingOtp || enteredOtp !== pendingOtp) { signupError.textContent = "Invalid OTP. Please check and try again."; return; }
      const users = getUsers();
      const newUser = { fullName: pendingSignup.fullName, username: pendingSignup.username, phone: pendingSignup.phone, email: pendingSignup.email, password: pendingSignup.password, role: pendingSignup.role, createdAt: new Date().toISOString(), verified: true };
      users.push(newUser); saveUsers(users);
      pendingSignup = null; pendingOtp = "";
      signupSuccess.textContent = "Account created successfully. You can log in now.";
      otpBox.classList.add("hidden");
      loginUsername.value = newUser.username; loginUserType.value = newUser.role; loginPassword.value = "";
      document.getElementById("signupForm").querySelectorAll("input").forEach(i => i.value = "");
      setTimeout(() => showAuthView("login"), 900);
    }

    /* ── Login ──────────────────────────────────────────────────────────────── */
    async function login() {
      loginError.textContent = "";
      const username = loginUsername.value.trim();
      const password = loginPassword.value;
      const role = loginUserType.value;
      if (!username || !password) { loginError.textContent = "Please enter both username and password."; return; }

      if (await backendAvailable()) {
        try {
          const res = await apiCall("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password, role }) });
          sessionStorage.setItem("resqmealToken", res.token);
          currentUser = { fullName: res.user.full_name, username: res.user.username, phone: res.user.phone, email: res.user.email, role: res.user.role, verified: true };
          sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(currentUser));
          enterDashboard(); return;
        } catch (err) { loginError.textContent = err.message; return; }
      }
      // Offline fallback
      const user = getUsers().find(item => normalizeUsername(item.username) === normalizeUsername(username));
      if (!user || user.password !== password || user.role !== role) { loginError.textContent = "Invalid username, password, or user type."; return; }
      currentUser = user;
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(user));
      enterDashboard();
    }

    function enterDashboard() {
      updateProfile(); applyRoleAccess();
      authScreen.classList.add("hidden"); appShell.classList.remove("app-hidden");
      window.scrollTo({ top: 0, behavior: "auto" });
      liveStatus.textContent = currentUser.role === "ngo" ? "NGO tools unlocked" : "Donor tools unlocked";
      location.hash = "dashboard";
      loadImpact(); renderRoute();
    }

    function logout() {
      sessionStorage.removeItem(SESSION_STORAGE_KEY); sessionStorage.removeItem("resqmealToken");
      currentUser = null;
      profilePanel.classList.add("hidden"); appShell.classList.add("app-hidden"); authScreen.classList.remove("hidden");
      loginPassword.value = ""; showAuthView("login"); window.scrollTo({ top: 0, behavior: "auto" });
    }

    function updateProfile() {
      const displayRole = roleLabel(currentUser.role);
      profileBtn.textContent = initials(currentUser.fullName);
      document.getElementById("profileName").textContent = currentUser.fullName;
      document.getElementById("profileRole").textContent = `${displayRole} account`;
      document.getElementById("profileContact").textContent = currentUser.email || currentUser.phone;
      document.getElementById("profileType").textContent = displayRole;
    }

    function canAccess(button) { return button.dataset.roles.split(" ").includes(currentUser.role); }

    function applyRoleAccess() {
      navButtons.forEach(button => button.classList.toggle("hidden", !canAccess(button)));
      const firstAllowed = [...navButtons].find(canAccess);
      if (firstAllowed) showTab(firstAllowed.dataset.tab);
    }

    function showTab(tabId) {
      const button = [...navButtons].find(item => item.dataset.tab === tabId);
      if (!button || !canAccess(button)) return;
      navButtons.forEach(item => item.classList.remove("active"));
      tabs.forEach(tab => tab.classList.add("hidden"));
      button.classList.add("active");
      document.getElementById(tabId).classList.remove("hidden");
      pageTitle.textContent = button.textContent;
      if (tabId === "impact") { liveStatus.textContent = "Impact updated from completed rescues"; loadImpact(); }
      else if (tabId === "ngo") { liveStatus.textContent = "Nearby donor predictions ready"; }
      else if (tabId === "donor") { liveStatus.textContent = "Ready to analyze a donation"; }
      else { liveStatus.textContent = "Tracking and route tools ready"; renderRoute(); }
    }

    /* ── Donor: Analyze & Notify ─────────────────────────────────────────────── */
    async function scoreDonation() {
      const meals = Number(document.getElementById("meals").value || 0);
      const hours = Number(document.getElementById("hours").value);
      const temp = document.getElementById("temp").value;
      const packaging = document.getElementById("packaging").value;

      if (await backendAvailable()) {
        try {
          liveStatus.textContent = "Analyzing with backend…";
          const res = await apiCall("/api/donations", {
            method: "POST",
            body: JSON.stringify({ donor_type: document.getElementById("donorType").value, food_name: document.getElementById("foodName").value, meals, hours, temperature: temp, packaging, location: document.getElementById("location").value }),
          });
          renderSafetyFromAPI(res.safety_score, res.safety_label, res.donation.ai_safety_analysis);
          renderMatchesFromAPI(res.ngo_matches);
          liveStatus.textContent = res.safety_score < 45 ? "Donation needs manual review" : "Nearby NGOs notified (backend)";
          return;
        } catch { /* fall through */ }
      }
      fallbackScore(meals, hours, temp, packaging);
    }

    function fallbackScore(meals, hours, temp, packaging) {
      let score = 54 + hours * 7 + Math.min(meals / 25, 8);
      if (temp === "cold") score += 8; if (temp === "hot") score += 5;
      if (packaging === "sealed") score += 12; else if (packaging === "covered") score += 4; else if (packaging === "open") score -= 24;
      if (hours <= 1) score -= 12;
      score = Math.max(18, Math.min(98, Math.round(score)));
      renderSafety(score, hours, packaging); renderMatches(score, meals, hours);
      liveStatus.textContent = score < 45 ? "Donation needs manual review" : "Nearby NGOs notified";
    }

    function renderSafetyFromAPI(score, label, aiAnalysis) {
      const ring = document.getElementById("scoreRing"); const text = document.getElementById("scoreText");
      const title = document.getElementById("safetyTitle"); const details = document.getElementById("safetyDetails"); const badge = document.getElementById("decisionBadge");
      ring.style.setProperty("--score", score);
      ring.style.background = `conic-gradient(${score < 45 ? "var(--red)" : score < 70 ? "var(--yellow)" : "var(--green)"} ${score}%, #e8eee9 0)`;
      text.textContent = score; title.textContent = label.title; 
      
      let detailsText = label.details;
      if (aiAnalysis) {
          detailsText += "\n\n🤖 Gemini AI Safety Advisor:\n" + aiAnalysis;
      }
      details.innerText = detailsText;
      
      badge.textContent = label.badge;
      badge.className = "badge" + (label.badge_style === "hot" ? " hot" : label.badge_style === "warn" ? " warn" : "");
    }

    function renderMatchesFromAPI(matches) {
      const cards = document.getElementById("matchCards"); cards.innerHTML = "";
      matches.forEach(ngo => {
        const dist = ngo.distance_km || ngo.distance || "?"; const need = ngo.need || "?"; const vehicle = ngo.vehicle || ""; const match = ngo.match_score || 0;
        cards.insertAdjacentHTML("beforeend", `<article class="card"><div class="card-head"><div><strong>${ngo.name}</strong><div class="muted small">${dist} km away \u00b7 needs ${need} meals \u00b7 ${vehicle}</div></div><span class="badge">${match}% match</span></div><div class="progress" aria-hidden="true"><b style="--w:${match}%"></b></div></article>`);
      });
    }

    function renderSafety(score, hours, packaging) {
      const ring = document.getElementById("scoreRing"); const text = document.getElementById("scoreText");
      const title = document.getElementById("safetyTitle"); const details = document.getElementById("safetyDetails"); const badge = document.getElementById("decisionBadge");
      ring.style.setProperty("--score", score);
      ring.style.background = `conic-gradient(${score < 45 ? "var(--red)" : score < 70 ? "var(--yellow)" : "var(--green)"} ${score}%, #e8eee9 0)`;
      text.textContent = score;
      if (score < 45) { title.textContent = "AI Food Safety Score: Needs review"; details.textContent = "Open or low-time food should be checked before matching. The app can pause alerts until admin approval."; badge.textContent = "Manual review"; badge.className = "badge hot"; }
      else if (hours <= 1) { title.textContent = "AI Food Safety Score: Emergency pickup"; details.textContent = "Food is acceptable but urgent. Volunteers within the smallest radius are notified first."; badge.textContent = "Emergency alert"; badge.className = "badge warn"; }
      else { title.textContent = "AI Food Safety Score: Good to donate"; details.textContent = `${packaging === "sealed" ? "Sealed" : "Covered"} food with ${hours} hours remaining is safe for fast pickup. NGOs with matching demand are prioritized.`; badge.textContent = "Approved for rescue"; badge.className = "badge"; }
    }

    function renderMatches(score, meals, hours) {
      const cards = document.getElementById("matchCards"); cards.innerHTML = "";
      ngos.map(ngo => {
        const quantityFit = 100 - Math.abs(ngo.need - meals) / Math.max(ngo.need, meals, 1) * 45;
        const urgencyBoost = hours <= 1 ? 18 / ngo.distance : 8 / ngo.distance;
        const match = Math.round(Math.min(99, score * .35 + quantityFit * .38 + urgencyBoost + (ngo.verified ? 7 : 0)));
        return { ...ngo, match };
      }).sort((a, b) => b.match - a.match).forEach(ngo => {
        cards.insertAdjacentHTML("beforeend", `<article class="card"><div class="card-head"><div><strong>${ngo.name}</strong><div class="muted small">${ngo.distance} km away \u00b7 needs ${ngo.need} meals \u00b7 ${ngo.vehicle}</div></div><span class="badge">${ngo.match}% match</span></div><div class="progress" aria-hidden="true"><b style="--w:${ngo.match}%"></b></div></article>`);
      });
    }

    /* ── NGO: Find Priority Donors ───────────────────────────────────────────── */
    async function rankDonors() {
      const people = Number(document.getElementById("people").value || 0);
      const radius = Number(document.getElementById("radius").value);
      const required = Math.ceil(people * 1.25);
      document.getElementById("requirementText").textContent = `Estimated food requirement: ${required} meals including buffer.`;
      const donorCards = document.getElementById("donorCards"); donorCards.innerHTML = "";

      if (await backendAvailable()) {
        try {
          const res = await apiCall("/api/ngo/requests", { method: "POST", body: JSON.stringify({ ngo_name: document.getElementById("ngoName").value, people_needed: people, radius_km: radius, storage_type: document.getElementById("storage").value, notes: document.getElementById("needNotes").value }) });
          res.ranked_donors.forEach(donor => {
            const dist = donor.distance_km || donor.distance || "?"; const avg = donor.avg_meals || donor.avg || "?"; const today = donor.today_meals || donor.today || "?"; const priority = donor.priority_score || 0; const hot = (donor.urgency || 0) > 85;
            donorCards.insertAdjacentHTML("beforeend", `<article class="card"><div class="card-head"><div><strong>${donor.name}</strong><div class="muted small">${dist} km \u00b7 average ${avg} leftover meals/day \u00b7 predicted today ${today}</div></div><span class="badge ${hot ? "hot" : "blue"}">${priority} priority</span></div><button class="secondary" onclick="document.getElementById('liveStatus').textContent='Request message sent to ${donor.name}'">Send request</button></article>`);
          });
          if (!donorCards.children.length) donorCards.innerHTML = `<div class="card"><strong>No donors inside this radius</strong><span class="muted small">Increase radius or turn on emergency alerts.</span></div>`;
          liveStatus.textContent = "Donor list fetched from backend"; return;
        } catch { /* fall through */ }
      }
      // Offline fallback
      donors.filter(d => d.distance <= radius).map(d => ({ ...d, priority: Math.round(d.today * .45 + d.avg * .35 + d.urgency * .2 - d.distance * 3) })).sort((a, b) => b.priority - a.priority).forEach(donor => {
        donorCards.insertAdjacentHTML("beforeend", `<article class="card"><div class="card-head"><div><strong>${donor.name}</strong><div class="muted small">${donor.distance} km \u00b7 average ${donor.avg} leftover meals/day \u00b7 predicted today ${donor.today}</div></div><span class="badge ${donor.urgency > 85 ? "hot" : "blue"}">${donor.priority} priority</span></div><button class="secondary" onclick="document.getElementById('liveStatus').textContent='Request message sent to ${donor.name}'">Send request</button></article>`);
      });
      if (!donorCards.children.length) donorCards.innerHTML = `<div class="card"><strong>No donors inside this radius</strong><span class="muted small">Increase radius or turn on emergency alerts.</span></div>`;
    }

    /* ── Routes & Tracking ───────────────────────────────────────────────────── */
    async function renderRoute() {
      const routeList = document.getElementById("routeList"); routeList.innerHTML = "";
      let stops = routeStops.map(s => ({ name: s[0], description: s[1], time: s[2] }));
      if (await backendAvailable()) {
        try { const res = await apiCall("/api/routes"); stops = res.stops; } catch { /* use seed */ }
      }
      stops.forEach(stop => {
        routeList.insertAdjacentHTML("beforeend", `<div class="stop"><div><strong>${stop.name}</strong><div class="muted small">${stop.description}</div></div><span class="badge blue">${stop.time}</span></div>`);
      });
    }

    /* ── Impact Dashboard ────────────────────────────────────────────────────── */
    async function loadImpact() {
      if (await backendAvailable()) {
        try {
          const [stats, chartData, board] = await Promise.all([apiCall("/api/impact/stats"), apiCall("/api/impact/chart"), apiCall("/api/impact/leaderboard")]);
          document.getElementById("mealMetric").textContent = Number(stats.meals_saved).toLocaleString();
          renderChartFromAPI(chartData); renderLeaderboardFromAPI(board); return;
        } catch { /* fall through */ }
      }
      renderChartFromAPI(days.map(d => ({ day: d[0], meals: d[1] })));
      renderLeaderboardFromAPI(leaders.map(l => ({ name: l[0], meals: l[1] })));
    }

    function renderChartFromAPI(chartData) {
      const chart = document.getElementById("chart"); chart.innerHTML = "";
      const max = Math.max(...chartData.map(d => d.meals));
      chartData.forEach(d => chart.insertAdjacentHTML("beforeend", `<div class="bar"><b style="--h:${d.meals / max * 100}%"></b><span>${d.day}<br>${d.meals}</span></div>`));
    }

    function renderLeaderboardFromAPI(boardData) {
      const board = document.getElementById("leaderboard"); board.innerHTML = "";
      boardData.forEach((entry, i) => {
        const label = typeof entry.meals === "number" ? `${Number(entry.meals).toLocaleString()} meals rescued` : entry.meals;
        board.insertAdjacentHTML("beforeend", `<div class="card"><div class="card-head"><strong>${i + 1}. ${entry.name}</strong><span class="badge">${label}</span></div></div>`);
      });
    }

    /* ── AI Chat ─────────────────────────────────────────────────────────────── */
    const aiKnowledge = [
      { keys: ["login", "log in", "signin", "sign in", "username", "password"], answer: "Login uses Username, Password, and User Type. The app checks those values against registered accounts stored in this browser before opening the dashboard." },
      { keys: ["signup", "sign up", "register", "account", "create"], answer: "Sign Up collects Full Name, Username, Phone Number, Email, Password, Confirm Password, and User Type. The account is created only after OTP verification." },
      { keys: ["otp", "verify", "verification", "phone"], answer: "The website sends a 6-digit OTP to the entered phone number during sign up. In this front-end demo, the OTP is shown on screen so the flow can be tested without an SMS service." },
      { keys: ["user type", "role", "ngo", "food donor", "donor"], answer: "There are two user types: NGO and Food Donor. Food Donors can use donation, route, and impact tools. NGOs can use demand, route, and impact tools." },
      { keys: ["donation", "surplus", "post food", "food safety", "safety score", "analyze"], answer: "The Donor Rescue section lets donors post surplus food details such as food type, meals, expiry time, temperature, packaging, and pickup location. The page calculates an AI Food Safety Score and recommends suitable NGO matches." },
      { keys: ["match", "matches", "smart match", "priority", "nearby"], answer: "Smart matching considers food safety score, quantity fit, urgency, distance, and NGO verification. Nearby NGOs shown on the site include Hope Shelter, Anbu Old Age Home, and Little Hands Home." },
      { keys: ["request", "demand", "shelter", "people", "radius"], answer: "The NGO Demand section lets NGOs request food by entering the shelter name, number of people to feed, search radius, storage availability, and notes. It then ranks nearby donors by priority." },
      { keys: ["route", "tracking", "pickup", "qr", "delivery"], answer: "Routes & Tracking shows an optimized pickup route, a donation tracking QR preview, pickup confirmation, expiry countdown, and NGO verification status." },
      { keys: ["impact", "dashboard", "meals saved", "co2", "leaderboard", "prediction"], answer: "The Impact Dashboard shows meals saved, CO2 prevented, money saved, fast rescues, leftover prediction, and a leaderboard for completed rescues." },
      { keys: ["data", "storage", "stored", "localstorage", "session"], answer: "This website stores registered account details in this browser's localStorage for future authentication and keeps the current logged-in session in sessionStorage." },
      { keys: ["what is", "about", "website", "resqmeal", "food rescue"], answer: "This website is an AI-powered smart food rescue network. It helps food donors share surplus food and helps NGOs find suitable nearby donations before food expires." }
    ];

    const privateQuestionWords = ["personal", "private", "password", "email", "phone", "number", "contact", "username", "account details", "stored user", "all users", "localstorage", "sessionstorage", "otp"];

    function openAiChat() {
      aiChatPanel.classList.remove("hidden");
      if (!aiChatLog.children.length) appendChatMessage("bot", "Hi, I can answer questions only about the details shown in this ResQmeal website. I cannot reveal registered users' private account details.");
      aiChatInput.focus();
    }

    function appendChatMessage(sender, text) {
      const message = document.createElement("div"); message.className = `chat-msg ${sender}`; message.textContent = text;
      aiChatLog.appendChild(message); aiChatLog.scrollTop = aiChatLog.scrollHeight; return message;
    }

    async function handleAiQuestion(event) {
      event.preventDefault();
      const question = aiChatInput.value.trim(); if (!question) return;
      appendChatMessage("user", question); aiChatInput.value = "";
      const thinking = appendChatMessage("bot", "Checking this website's details...");
      thinking.textContent = await answerWithModel(question);
      aiChatLog.scrollTop = aiChatLog.scrollHeight;
    }

    async function answerWithModel(question) {
      try {
        const response = await fetch(API_BASE + "/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }), signal: AbortSignal.timeout(3000) });
        if (!response.ok) throw new Error("unavailable");
        const data = await response.json();
        return data.answer || answerFromWebsite(question);
      } catch { return answerFromWebsite(question); }
    }

    function answerFromWebsite(question) {
      const text = question.toLowerCase();
      const asksForPrivateData = privateQuestionWords.some(word => text.includes(word)) && /\b(show|give|list|reveal|view|see|display|fetch|read|export)\b/.test(text);
      if (asksForPrivateData) return "I can't reveal personal account details, stored user records, passwords, OTPs, phone numbers, emails, or contacts. I can explain how the website protects and uses those fields.";
      const match = aiKnowledge.map(item => ({ answer: item.answer, score: item.keys.reduce((t, k) => t + (text.includes(k) ? 1 : 0), 0) })).sort((a, b) => b.score - a.score)[0];
      if (match && match.score > 0) return match.answer;
      return "I can only answer from the content in this website: login, sign up, OTP verification, donor rescue, NGO demand, routes, tracking, impact metrics, and the role-based dashboard. Please ask about one of those areas.";
    }

    document.getElementById("analyzeBtn").addEventListener("click", scoreDonation);
    document.getElementById("sampleBtn").addEventListener("click", () => {
      document.getElementById("donorType").value = "Household function";
      document.getElementById("foodName").value = "Idli, sambar and lemon rice";
      document.getElementById("meals").value = 45;
      document.getElementById("hours").value = 1;
      document.getElementById("temp").value = "room";
      document.getElementById("packaging").value = "covered";
      document.getElementById("location").value = "Velachery Housewarming Event";
      scoreDonation();
    });
    document.getElementById("rankBtn").addEventListener("click", rankDonors);

    function restoreSession() {
      const hash = location.hash.replace("#", "");
      if (hash === "signup") showAuthView("signup"); else showAuthView("login");
      try {
        const savedUser = JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEY));
        if (savedUser && savedUser.username) {
          currentUser = savedUser; updateProfile(); applyRoleAccess();
          authScreen.classList.add("hidden"); appShell.classList.remove("app-hidden");
          loadImpact(); renderRoute();
        }
      } catch { sessionStorage.removeItem(SESSION_STORAGE_KEY); sessionStorage.removeItem("resqmealToken"); }
    }

    window.addEventListener("hashchange", () => {
      const hash = location.hash.replace("#", "");
      if (hash === "signup" || hash === "login") { appShell.classList.add("app-hidden"); authScreen.classList.remove("hidden"); showAuthView(hash); }
    });

    fallbackScore(120, 4, "room", "sealed");
    rankDonors();
    renderRoute();
    loadImpact();
    restoreSession();

    let remaining = 222;
    setInterval(() => {
      remaining = Math.max(0, remaining - 1);
      const h = Math.floor(remaining / 60); const m = remaining % 60;
      document.getElementById("countdown").textContent = `Delivery should finish within ${h}h ${String(m).padStart(2, "0")}m.`;
    }, 60000);
  </script>
</body>
</html>"""

# Read current file
with open(SRC, encoding="utf-8") as f:
    content = f.read()

# Find script tag start
script_pos = content.index("<script>")
# Everything before script tag (include the 2 spaces of indentation)
before_script = content[:script_pos]

# Write patched file
patched = before_script + NEW_SCRIPT.lstrip() + "\n"
with open(SRC, "w", encoding="utf-8") as f:
    f.write(patched)

print("OK — frontend patched")
print(f"New size: {len(patched)} bytes")
