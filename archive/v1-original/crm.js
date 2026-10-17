// ==========================
// Global state
// ==========================
let investors = [];
let filteredInvestors = [];
let visibleCount = 10;
let isExpanded = false;

// ==========================
// Load CSV on page load
// ==========================
document.addEventListener("DOMContentLoaded", () => {
  // הכי חשוב: להשתמש בנתיב יחסי (הקובץ באותה תיקייה של crm.html)
  fetch("investors_data.csv")
    .then((res) => {
      if (!res.ok) throw new Error("Failed to load investors_data.csv");
      return res.text();
    })
    .then((csvText) => {
      const parsed = Papa.parse(csvText, {
        header: true,
        skipEmptyLines: true
      });

      // ניקוי שורות ריקות (לפעמים ב-CSV יש שורה אחרונה ריקה)
      investors = (parsed.data || []).filter((row) =>
        Object.values(row).some((v) => String(v || "").trim() !== "")
      );

      filteredInvestors = [...investors];

      populateSectorFilter();
      renderInvestors();
    })
    .catch((err) => console.error("CSV error:", err));
});

// ==========================
// Populate sector dropdown
// ==========================
function populateSectorFilter() {
  const select = document.getElementById("sectorFilter");
  if (!select) return; // אם אין פילטר בעמוד עדיין, לא להפיל את הקוד

  select.innerHTML = `<option value="">All sectors</option>`;
  const sectors = new Set();

  investors.forEach((inv) => {
    const sectorsStr = inv.Sectors || inv.sectors || "";
    if (!sectorsStr) return;

    sectorsStr.split(",").forEach((sec) => {
      const clean = sec.trim();
      if (clean) sectors.add(clean);
    });
  });

  [...sectors].sort().forEach((sec) => {
    const option = document.createElement("option");
    option.value = sec;
    option.innerText = sec;
    select.appendChild(option);
  });
}

// ==========================
// Filters (search + sector)
// ==========================
function applyFilters() {
  const searchEl = document.getElementById("searchInput");
  const sectorEl = document.getElementById("sectorFilter");

  const search = (searchEl?.value || "").toLowerCase().trim();
  const sector = (sectorEl?.value || "").trim();

  filteredInvestors = investors.filter((inv) => {
    const firstName = (inv.FirstName || inv.firstName || "").trim();
    const lastName = (inv.LastName || inv.lastName || "").trim();
    const fullName = `${firstName} ${lastName}`.toLowerCase();

    const sectorsStr = inv.Sectors || inv.sectors || "";

    const matchesName = !search || fullName.includes(search);
    const matchesSector = !sector || (sectorsStr && sectorsStr.includes(sector));

    return matchesName && matchesSector;
  });

  visibleCount = 10;
  renderInvestors();
}

function renderInvestors() {
  const container = document.getElementById("investorList");
  if (!container) return;

  container.innerHTML = "";

  filteredInvestors.slice(0, visibleCount).forEach((inv, index) => {
    const firstName = inv.FirstName || "";
    const lastName = inv.LastName || "";
    if (!firstName && !lastName) return;

    const initials =
      (firstName[0] || "").toUpperCase() +
      (lastName[0] || "").toUpperCase();

    container.innerHTML += `
      <div class="investor-card">
        <h3>${firstName} ${lastName}</h3>

        <div class="sectors">
          ${renderSectorIcons(inv.Sectors)}
        </div>

        <div class="actions">
          <button class="btn-outline" onclick="toggleDetails(${index})">
            More details
          </button>
          <button class="btn-primary"
            onclick="openContactForm('${firstName} ${lastName}')">
            Send message
          </button>
        </div>

        <div class="investor-details hidden" id="details-${index}">
          ${renderExtraDetails(inv)}
        </div>
      </div>
    `;
  });

  // ---- See more / less logic ----
  const btn = document.getElementById("seeMoreBtn");
  if (!btn) return;

  if (filteredInvestors.length <= 10) {
    btn.style.display = "none";
  } else {
    btn.style.display = "inline-block";
    btn.innerText =
      visibleCount < filteredInvestors.length
        ? "See more"
        : "See less";
  }
}


// ==========================
// Sector icons
// ==========================
function renderSectorIcons(sectors) {
  const sectorsStr = (sectors || "").trim();
  if (!sectorsStr) return "";

  return sectorsStr
    .split(",")
    .map((sec) => sec.trim())
    .filter(Boolean)
    .map((s) => `<span class="sector-tag">${getSectorIcon(s)} ${escapeHtml(s)}</span>`)
    .join("");
}

function getSectorIcon(sector) {
  const icons = {
    "AI": "🤖",
    "Artificial Intelligence": "🧠",
    "FinTech": "💰",
    "Cyber": "🛡️",
    "Cybersecurity": "🔐",
    "Health": "🩺",
    "HealthTech": "❤️",
    "Climate": "🌱",
    "Energy": "⚡",
    "Renewable Energy": "♻️",
    "E-commerce": "🛒",
    "Retail": "🏬",
    "SaaS": "☁️",
    "Software": "💻",
    "PropTech": "🏢",
    "Real Estate": "🏠",
    "Automotive": "🚗",
    "Industrial": "🏭",
    "Robotics": "🤖",
    "Data": "📊",
    "Cloud": "☁️",
    "Mobile": "📱",
    "Security": "🔒",
    "Payments": "💳",
    "Quantum": "⚛️"
  };

  return icons[sector] || "✨";
}


// ==========================
// UI helpers
// ==========================
function toggleDetails(index) {
  const el = document.getElementById(`details-${index}`);
  if (el) el.classList.toggle("hidden");
}

function openContactForm(name) {
  const modal = document.getElementById("contactModal");
  if (!modal) return;

  const title = modal.querySelector("h2");
  if (title) title.innerText = "Request Introduction to " + name;

  modal.style.display = "flex";
}

function closeContactForm() {
  const modal = document.getElementById("contactModal");
  if (modal) modal.style.display = "none";
}

// ==========================
// Small safety helpers
// ==========================
function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(str) {
  return escapeHtml(str).replaceAll("`", "&#096;");
}

function safeUrl(url) {
  const u = String(url || "").trim();
  if (!u) return "#";
  if (u.startsWith("http://") || u.startsWith("https://")) return u;
  return "https://" + u.replace(/^\/+/, "");
}

function renderExtraDetails(inv) {
  const ignored = ["FirstName", "LastName", "Sectors"];
  let html = "";

  Object.entries(inv).forEach(([key, value]) => {
    if (!value || ignored.includes(key)) return;
    html += `<p><strong>${key}:</strong> ${value}</p>`;
  });

  return html || "<p>No additional details</p>";
}
function toggleSeeMore() {
  // אם כרגע מוצגים פחות מהכול -> הצג הכול
  if (visibleCount < filteredInvestors.length) {
    visibleCount = filteredInvestors.length;
  } else {
    // אחרת -> חזור לברירת מחדל (10)
    visibleCount = 10;
  }

  renderInvestors();
}
function subscribeNewsletter() {
  const emailInput = document.getElementById("newsletterEmail");
  const email = emailInput.value.trim();

  if (!email || !email.includes("@")) {
    alert("Please enter a valid email address");
    return;
  }

  // שלב ראשון – דמו
  alert("🎉 Thank you for subscribing to Genesis Newsletter!");

  emailInput.value = "";

  // 🔜 בהמשך:
  // שליחה ל־Backend / Firebase / Mailchimp / Google Sheet
}
const mentors = [
  {
    name: "Bill Macaitis",
    title: "Former CMO at Slack, Zendesk, Salesforce",
    highlight: "5 exits",
    sectors: ["SaaS", "Marketing", "Growth"],
  },
  {
    name: "Michael Coates",
    title: "3x CISO at Twitter, Mozilla, CoinList",
    highlight: "Cybersecurity Investor",
    sectors: ["Cybersecurity", "Security"],
  },
  {
    name: "Daniel Krivelevich",
    title: "Co-Founder & CTO at Cider Security (acq. by PANW)",
    highlight: "Investor",
    sectors: ["Cybersecurity", "DevSecOps"],
  },
  {
    name: "Avishag Bohbot",
    title: "Early Investor at Deci AI, XTEND",
    highlight: "AI & Defense Tech",
    sectors: ["AI", "Defense"],
  },
  {
    name: "Gali Arnon",
    title: "CBO at Fiverr",
    highlight: "Marketplace & Growth",
    sectors: ["Marketplace", "Growth"],
  },
  {
    name: "Nitin Bhat",
    title: "Former CPO at Workiva",
    highlight: "Product Strategy",
    sectors: ["Product", "SaaS"],
  },
  {
    name: "Guy Gamzu",
    title: "Early Investor at Fiverr, eToro, Moon Active",
    highlight: "FinTech & Gaming",
    sectors: ["FinTech", "Gaming"],
  },
  {
    name: "Hila Goldman",
    title: "CEO & Co-Founder at DiA (acq. by Philips)",
    highlight: "HealthTech",
    sectors: ["HealthTech"],
  },
  {
    name: "Mickey Haslavsky",
    title: "CEO & Founder at enso",
    highlight: "Automation & Ops",
    sectors: ["Automation", "Operations"],
  },
  {
    name: "Asaf Gazit",
    title: "Co-Founder & CEO at Ludeo",
    highlight: "Gaming & Interactive Media",
    sectors: ["Gaming", "Media"],
  }
];

const mentorImages = {
  "Bill Macaitis": "../static/png/mentors/bill.png",
  "Michael Coates": "../static/png/mentors/michael.png",
  "Daniel Krivelevich": "../static/png/mentors/daniel.png",
  "Avishag Bohbot": "../static/png/mentors/avishag.png",
  "Gali Arnon": "../static/png/mentors/gali.png",
  "Guy Gamzu": "../static/png/mentors/guy.png",
  "Hila Goldman": "../static/png/mentors/hila.png",
  "Mickey Haslavsky": "../static/png/mentors/mickey.png",
  "Nitin Bhat": "../static/png/mentors/nitin.png",
  "Asaf Gazit": "../static/png/mentors/asaf.png"
};

};

function renderMentors(list = mentors) {
  const container = document.getElementById("mentorList");
  if (!container) return;

  container.innerHTML = "";

  list.forEach((m) => {
    const imgHtml = mentorImages[m.name]
      ? `<img src="${mentorImages[m.name]}" alt="${m.name}" class="mentor-img">`
      : `<div class="mentor-placeholder">👤</div>`;

    container.innerHTML += `
      <div class="mentor-card">
        <div class="mentor-avatar">
          ${imgHtml}
        </div>

        <h3>${m.name}</h3>
        <p class="mentor-title">${m.title}</p>
        <p class="mentor-highlight">${m.highlight}</p>

        <div class="sectors">
          ${m.sectors.map(s => `<span class="sector-tag">${s}</span>`).join("")}
        </div>

        <button class="btn-outline"
          onclick="openContactForm('${m.name}', 'general')">
          Request mentorship
        </button>
      </div>
    `;
  });
}

document.addEventListener("DOMContentLoaded", () => renderMentors());

const benefits = [
  {
    name: "Atlassian",
    logo: "static/png/benefits/atlassian.png",
    category: "Product & Dev",
    offer: "12 months 50% discount",
    link: "https://www.atlassian.com/startups",
    tag: "Perks",
    steps: [
      "Apply via Atlassian for Startups",
      "Verify startup eligibility",
      "Activate discount"
    ]
  },
  {
    name: "HubSpot",
    logo: "static/png/benefits/hubspot.png",
    category: "CRM & Marketing",
    offer: "Up to 90% discount",
    link: "https://www.hubspot.com/startups",
    tag: "Discount",
    steps: [
      "Register via HubSpot Startups",
      "Verify company",
      "Redeem discount"
    ]
  },
  {
    name: "Lusha",
    logo: "static/png/benefits/lusha.png",
    category: "Competitive Intelligence",
    offer: "5,000 credits",
    link: "https://www.lusha.com/",
    tag: "Perks",
    steps: [
      "Register using the link",
      "Email team@genesis-accelerator.com",
      "Include startup name & cohort"
    ]
  },
  {
    name: "Intercom",
    logo: "static/png/benefits/intercom.png",
    category: "Customer Support",
    offer: "Free advanced plan for startups",
    link: "https://www.intercom.com/startups",
    tag: "Perks",
    steps: [
      "Apply via Intercom Startups",
      "Get approval",
      "Activate plan"
    ]
  },
  {
    name: "Notion",
    logo: "static/png/benefits/notion.png",
    category: "Productivity",
    offer: "6 months Business Plan free",
    link: "https://www.notion.so/startups",
    tag: "Perks",
    steps: [
      "Apply via Notion for Startups",
      "Login with company email",
      "Activate Business Plan"
    ]
  },
  {
    name: "Deel",
    logo: "static/png/benefits/deel.png",
    category: "HR & Payroll",
    offer: "$5,000 credits",
    link: "https://www.deel.com/startups",
    tag: "Credits",
    steps: [
      "Contact Deel",
      "Mention Genesis",
      "Receive credits"
    ]
  },
  {
    name: "Vercel",
    logo: "static/png/benefits/vercel.png",
    category: "Hosting & DevOps",
    offer: "Free Pro plan",
    link: "https://vercel.com/startups",
    tag: "Perks",
    steps: [
      "Apply via Vercel Startups",
      "Verify startup",
      "Upgrade to Pro"
    ]
  },
  {
    name: "Superhuman",
    logo: "static/png/benefits/superhuman.png",
    category: "Productivity",
    offer: "1 year free Business plan",
    link: "https://superhuman.com/startups",
    tag: "Perks",
    steps: [
      "Register via Superhuman",
      "Apply as startup",
      "Activate benefit"
    ]
  },
  {
    name: "Linear",
    logo: "static/png/benefits/linear.png",
    category: "Product Management",
    offer: "Free months",
    link: "https://linear.app/startups",
    tag: "Perks",
    steps: [
      "Create Linear account",
      "Apply as startup",
      "Activate benefit"
    ]
  },
  {
    name: "Similarweb",
    logo: "static/png/benefits/similarweb.png",
    category: "Market Intelligence",
    offer: "30% discount",
    link: "https://www.similarweb.com/startups",
    tag: "Discount",
    steps: [
      "Apply via Similarweb",
      "Verify startup",
      "Redeem discount"
    ]
  },
  {
    name: "Mercury",
    logo: "static/png/benefits/mercury.png",
    category: "Banking",
    offer: "$100 credit",
    link: "https://mercury.com/startups",
    tag: "Perks",
    steps: [
      "Open Mercury account",
      "Get approval",
      "Receive credit"
    ]
  },
  {
    name: "Google Cloud",
    logo: "static/png/benefits/googlecloud.png",
    category: "Cloud",
    offer: "$2,000-$25,000 credits",
    link: "https://cloud.google.com/startup",
    tag: "Credits",
    steps: [
      "Apply via Google for Startups",
      "Verify company",
      "Receive credits"
    ]
  },
  {
    name: "Mobbin",
    logo: "static/png/benefits/mobbin.png",
    category: "Design",
    offer: "Free 6 months",
    link: "https://mobbin.com",
    tag: "Perks",
    steps: [
      "Register on Mobbin",
      "Apply via Genesis",
      "Activate plan"
    ]
  }
];

function renderBenefits() {
  const grid = document.getElementById("benefitsGrid");
  if (!grid) return;

  grid.innerHTML = "";

  benefits.forEach((b, index) => {
    grid.innerHTML += `
      <div class="card perk-card" onclick="openBenefit(${index})">
        <img src="static/png/benefits/${b.logo}" class="perk-logo" alt="${b.name}">
        <h3>${b.name}</h3>
        <p>${b.offer}</p>
        <span class="perk-tag">${b.tag}</span>
      </div>
    `;
  });
}

document.addEventListener("DOMContentLoaded", renderBenefits);

function openBenefit(index) {
  const b = benefits[index];

  document.getElementById("modalLogo").src =
    `static/png/benefits/${b.logo}`;

  document.getElementById("modalName").innerText = b.name;
  document.getElementById("modalCategory").innerText = b.category;
  document.getElementById("modalLink").href = b.link;
  document.getElementById("modalOffer").innerText = b.offer;

  const steps = document.getElementById("modalSteps");
  steps.innerHTML = "";
  b.steps.forEach(s => {
    steps.innerHTML += `<li>${s}</li>`;
  });

  document.getElementById("benefitModal").style.display = "flex";
}


function closeBenefitModal(e) {
  if (e.target.id === "benefitModal") {
    document.getElementById("benefitModal").style.display = "none";
  }
}
function openInvestorModal(index) {
  const inv = investors[index];

  document.getElementById("modalInvestorName").textContent = inv.name;
  document.getElementById("modalInvestorTitle").textContent = inv.title;
  document.getElementById("modalInvestorBio").textContent = inv.bio;

  document.getElementById("investorModal").classList.remove("hidden");
}


function closeInvestorModal() {
  document.getElementById("investorModal").classList.add("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("investorModal")?.classList.add("hidden");
});

function openContactForm(name, type = 'general') {
    const modal = document.getElementById("contactModal");
    if (!modal) return;

    const titleEl = document.getElementById("contactTitle") || modal.querySelector("h2");
    const startupFields = document.getElementById("startupOnlyFields");

    if (titleEl) titleEl.innerText = "Connect with " + name;

    // הצגת שדה נוסף רק לסטארטאפים
    if (type === 'startup') {
        startupFields?.classList.remove("hidden");
    } else {
        startupFields?.classList.add("hidden");
    }

    modal.style.display = "flex";
}

function closeContactForm() {
    const modal = document.getElementById("contactModal");
    if (modal) modal.style.display = "none";
}

// סינון מנטורים
function filterMentors() {
    const term = document.getElementById("mentorSearch").value.toLowerCase();
    const filtered = mentors.filter(m =>
        m.name.toLowerCase().includes(term) ||
        m.sectors.some(s => s.toLowerCase().includes(term))
    );
    renderMentors(filtered);
}

// סינון סטארטאפים (צריך להגדיר מערך startups ב-JS אם הוא לא קיים)
function filterStartups() {
    const term = document.getElementById("startupSearch").value.toLowerCase();
    // וודא שיש לך מערך בשם 'startups' בקוד
    const filtered = startups.filter(s => s.name.toLowerCase().includes(term));
    renderStartups(filtered);
}
