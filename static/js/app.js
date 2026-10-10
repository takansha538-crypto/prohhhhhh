(function () {
  const byId = (id) => document.getElementById(id);

  document.querySelectorAll(".toast").forEach((t) => {
    setTimeout(() => {
      t.style.opacity = "0";
      setTimeout(() => t.remove(), 400);
    }, 4200);
  });

  const navToggle = byId("navToggle");
  const mobileNav = byId("mobileNav");
  if (navToggle && mobileNav) {
    navToggle.addEventListener("click", () => {
      const open = !mobileNav.hidden;
      mobileNav.hidden = open;
      navToggle.setAttribute("aria-expanded", String(!open));
    });
  }

  function bindMenu(btnId, menuId) {
    const btn = byId(btnId);
    const menu = byId(menuId);
    if (!btn || !menu) return;
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const willOpen = menu.hidden;
      document.querySelectorAll(".dropdown").forEach((d) => {
        d.hidden = true;
      });
      menu.hidden = !willOpen;
      btn.setAttribute("aria-expanded", String(willOpen));
    });
  }
  bindMenu("menuBtn", "userMenu");
  bindMenu("notifBtn", "notifMenu");

  document.addEventListener("click", () => {
    document.querySelectorAll(".dropdown").forEach((d) => {
      d.hidden = true;
    });
  });
  document.querySelectorAll(".dropdown").forEach((d) => {
    d.addEventListener("click", (e) => e.stopPropagation());
  });

  const notifBtn = byId("notifBtn");
  const notifList = byId("notifList");
  if (notifBtn && notifList) {
    notifBtn.addEventListener("click", () => {
      fetch("/notifications/partial")
        .then((r) => r.text())
        .then((html) => {
          notifList.innerHTML = html;
        })
        .catch(() => {
          notifList.textContent = "Could not load notifications.";
        });
    });
  }

  document.querySelectorAll("[data-count]").forEach((el) => {
    const target = Number(el.getAttribute("data-count"));
    if (!target) return;
    let n = 0;
    const step = Math.max(1, Math.round(target / 40));
    const tick = () => {
      n = Math.min(target, n + step);
      el.textContent = n.toLocaleString();
      if (n < target) requestAnimationFrame(tick);
    };
    tick();
  });

  document.querySelectorAll(".tabbed").forEach((root) => {
    const buttons = root.querySelectorAll("[data-tab]");
    const panes = root.querySelectorAll("[data-pane]");
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-tab");
        buttons.forEach((b) => b.classList.toggle("on", b === btn));
        panes.forEach((p) => {
          p.hidden = p.getAttribute("data-pane") !== id;
        });
      });
    });
  });
})();
