/* Scholarship Hub — progressive enhancement only. Everything works without JS. */
(function () {
  "use strict";

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  /* ---------------------------------------------------------------------- */
  /* Theme                                                                  */
  /* ---------------------------------------------------------------------- */
  const root = document.documentElement;
  const themeBtn = $("#themeToggle");
  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    try { localStorage.setItem("sh-theme", theme); } catch (e) {}
  }
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      setTheme(root.getAttribute("data-theme") === "light" ? "dark" : "light");
    });
  }
  if (window.matchMedia) {
    const mq = window.matchMedia("(prefers-color-scheme: light)");
    if (mq.matches && !localStorage.getItem("sh-theme")) setTheme("light");
  }

  /* ---------------------------------------------------------------------- */
  /* Sticky nav                                                             */
  /* ---------------------------------------------------------------------- */
  const nav = $("#navbar");
  if (nav) {
    const onScroll = () => nav.classList.toggle("is-stuck", window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------------------------------------------------------------------- */
  /* Mobile menu                                                            */
  /* ---------------------------------------------------------------------- */
  const menuBtn = $("#menuToggle");
  const links = $("#navLinks");
  if (menuBtn && links) {
    menuBtn.addEventListener("click", () => {
      const open = links.classList.toggle("is-open");
      menuBtn.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("click", (e) => {
      if (!links.contains(e.target) && !menuBtn.contains(e.target)) {
        links.classList.remove("is-open");
        menuBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------------------------------------------------------------------- */
  /* User dropdown                                                          */
  /* ---------------------------------------------------------------------- */
  const userMenu = $("[data-user-menu]");
  if (userMenu) {
    const btn = $("[data-user-btn]", userMenu);
    btn?.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = userMenu.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("click", (e) => {
      if (!userMenu.contains(e.target)) userMenu.classList.remove("is-open");
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") userMenu.classList.remove("is-open");
    });
  }

  /* ---------------------------------------------------------------------- */
  /* Toasts                                                                 */
  /* ---------------------------------------------------------------------- */
  $$(".toast-close").forEach((btn) =>
    btn.addEventListener("click", () => btn.closest(".toast")?.remove())
  );

  /* ---------------------------------------------------------------------- */
  /* Reveal on scroll                                                       */
  /* ---------------------------------------------------------------------- */
  const revealItems = $$(".reveal");
  if ("IntersectionObserver" in window && revealItems.length) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px" }
    );
    revealItems.forEach((el) => io.observe(el));
  } else {
    revealItems.forEach((el) => el.classList.add("is-in"));
  }

  /* ---------------------------------------------------------------------- */
  /* Copy buttons                                                           */
  /* ---------------------------------------------------------------------- */
  $$("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const value = btn.getAttribute("data-copy");
      try {
        await navigator.clipboard.writeText(value);
        const original = btn.getAttribute("title") || "";
        btn.setAttribute("title", "Copied!");
        btn.classList.add("is-copied");
        setTimeout(() => {
          btn.classList.remove("is-copied");
          btn.setAttribute("title", original);
        }, 1600);
      } catch (e) {
        window.prompt("Copy this value", value);
      }
    });
  });

  /* ---------------------------------------------------------------------- */
  /* Confirm destructive actions                                            */
  /* ---------------------------------------------------------------------- */
  $$("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!window.confirm(form.getAttribute("data-confirm"))) e.preventDefault();
    });
  });

  /* ---------------------------------------------------------------------- */
  /* Auto-submit filters                                                    */
  /* ---------------------------------------------------------------------- */
  $$("[data-autosubmit]").forEach((el) => {
    el.addEventListener("change", () => el.closest("form")?.submit());
  });

  /* ---------------------------------------------------------------------- */
  /* Search suggestions (hero)                                              */
  /* ---------------------------------------------------------------------- */
  const searchWrap = $("[data-search]");
  if (searchWrap) {
    const input = $("input[type=search]", searchWrap);
    const panel = $(".suggest-panel", searchWrap);
    let timer = null;
    let controller = null;

    function hide() {
      if (panel) {
        panel.classList.remove("is-open");
        panel.innerHTML = "";
      }
    }

    function render(items, query) {
      if (!panel) return;
      if (!items.length) {
        panel.innerHTML =
          '<div class="suggest-empty">No scheme matches “' + escapeHtml(query) + '”. Try “girls”, “SC”, “engineering” or a state.</div>';
      } else {
        panel.innerHTML =
          items
            .map(
              (s) =>
                '<a class="suggest-item" href="/scholarships/' + s.slug + '">' +
                '<span class="suggest-icon"><svg class="ico"><use href="#i-graduation"></use></svg></span>' +
                '<span class="suggest-body"><strong>' + escapeHtml(s.name) + "</strong>" +
                "<small>" + escapeHtml(s.provider) + " · " + escapeHtml(s.state) + "</small></span>" +
                '<span class="suggest-amt">' + escapeHtml(s.amount) + "</span></a>"
            )
            .join("") +
          '<a class="suggest-all" href="/scholarships?q=' + encodeURIComponent(query) + '">See all matches <svg class="ico"><use href="#i-arrow-right"></use></svg></a>';
      }
      panel.classList.add("is-open");
    }

    input?.addEventListener("input", () => {
      const q = input.value.trim();
      clearTimeout(timer);
      if (q.length < 2) return hide();
      timer = setTimeout(async () => {
        controller?.abort();
        controller = new AbortController();
        try {
          const res = await fetch("/api/scholarships?q=" + encodeURIComponent(q) + "&limit=5", {
            signal: controller.signal,
            headers: { Accept: "application/json" },
          });
          if (!res.ok) return;
          const data = await res.json();
          render(data.results || [], q);
        } catch (err) {
          /* request aborted or offline — ignore */
        }
      }, 220);
    });

    document.addEventListener("click", (e) => {
      if (!searchWrap.contains(e.target)) hide();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") hide();
    });
  }

  function escapeHtml(str) {
    return String(str || "").replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[ch]));
  }

  /* ---------------------------------------------------------------------- */
  /* Animate progress bars on load                                          */
  /* ---------------------------------------------------------------------- */
  $$(".progress > span[data-value]").forEach((bar) => {
    const target = bar.getAttribute("data-value") + "%";
    bar.style.width = "0%";
    requestAnimationFrame(() => setTimeout(() => (bar.style.width = target), 80));
  });
})();
