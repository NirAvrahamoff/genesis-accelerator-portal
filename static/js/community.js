// Community portal: client-side filtering and the introduction-request dialog.
(function () {
  const csrf = document.querySelector('meta[name="csrf-token"]').content;

  function filterCards(items, emptyEl, predicate) {
    let shown = 0;
    items.forEach((el) => {
      const match = predicate(el);
      el.hidden = !match;
      if (match) shown += 1;
    });
    emptyEl.hidden = shown > 0;
  }

  // Mentors
  const mentorSearch = document.getElementById("mentorSearch");
  const mentors = document.querySelectorAll("#mentorList [data-search]");
  mentorSearch.addEventListener("input", () => {
    const term = mentorSearch.value.trim().toLowerCase();
    filterCards(mentors, document.getElementById("mentorEmpty"), (el) => el.dataset.search.includes(term));
  });

  // Investors
  const investorSearch = document.getElementById("investorSearch");
  const investorSector = document.getElementById("investorSector");
  const investors = document.querySelectorAll("#investorList [data-search]");
  function filterInvestors() {
    const term = investorSearch.value.trim().toLowerCase();
    const sector = investorSector.value;
    filterCards(investors, document.getElementById("investorEmpty"), (el) =>
      el.dataset.search.includes(term) && (!sector || el.dataset.sectors.split("|").includes(sector)));
  }
  investorSearch.addEventListener("input", filterInvestors);
  investorSector.addEventListener("change", filterInvestors);

  // Introduction requests
  const dialog = document.getElementById("introDialog");
  const form = document.getElementById("introForm");
  const done = document.getElementById("introDone");
  const error = document.getElementById("introError");
  const titles = { startup: "Contact", mentor: "Request mentorship from", investor: "Request an introduction to" };

  document.querySelectorAll("[data-intro]").forEach((btn) => {
    btn.addEventListener("click", () => {
      form.reset();
      form.hidden = false;
      done.hidden = true;
      error.hidden = true;
      form.target_type.value = btn.dataset.intro;
      form.target_name.value = btn.dataset.name;
      document.getElementById("introTitle").textContent = `${titles[btn.dataset.intro]} ${btn.dataset.name}`;
      dialog.showModal();
    });
  });
  document.getElementById("introCancel").addEventListener("click", () => dialog.close());
  document.getElementById("introClose").addEventListener("click", () => dialog.close());

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await fetch("/community/intro", {
      method: "POST",
      headers: { "X-CSRF-Token": csrf },
      body: new FormData(form),
    });
    const result = await response.json().catch(() => ({ ok: false }));
    if (result.ok) {
      form.hidden = true;
      done.hidden = false;
    } else {
      error.textContent = result.error || "Something went wrong. Please try again.";
      error.hidden = false;
    }
  });
})();
