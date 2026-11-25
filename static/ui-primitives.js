/**
 * Reusable UI Primitives & Uniform 1.75px Stroke Icon Set
 * Monochrome Soft Bento & Frosted Glassmorphism System
 */
(function () {
  "use strict";

  const ICON_PATHS = {
    baby: '<circle cx="12" cy="8" r="3.5"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0"/><path d="M12 4.5V3"/><path d="M9.5 8h.01"/><path d="M14.5 8h.01"/>',
    heartOff: '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="m2 2 20 20"/>',
    activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    fileText: '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/>',
    filePlus: '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>',
    layers: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    layoutGrid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>',
    listChecks: '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
    sliders: '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="2" y1="14" x2="6" y2="14"/><line x1="10" y1="8" x2="14" y2="8"/><line x1="18" y1="16" x2="22" y2="16"/>',
    cpu: '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    shieldCheck: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/>',
    lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    externalLink: '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',
    refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    moreHorizontal: '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
    menu: '<line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="18" x2="20" y2="18"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    chevronDown: '<path d="m6 9 6 6 6-6"/>',
    eye: '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
    trash: '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
    check: '<polyline points="20 6 9 17 4 12"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    sparkles: '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>'
  };

  /**
   * 1. Uniform Thin-Stroke SVG Icon Primitive (<svg-icon name="..." size="16">)
   */
  class SvgIcon extends HTMLElement {
    static get observedAttributes() {
      return ["name", "size"];
    }
    connectedCallback() {
      this.render();
    }
    attributeChangedCallback() {
      this.render();
    }
    render() {
      const name = this.getAttribute("name") || "info";
      const size = this.getAttribute("size") || "16";
      const paths = ICON_PATHS[name] || ICON_PATHS.info;
      this.style.display = "inline-flex";
      this.style.alignItems = "center";
      this.style.justifyContent = "center";
      this.style.flexShrink = "0";
      this.innerHTML = `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
    }
  }

  /**
   * 2. BentoCard Primitive (<bento-card variant="dark | light | muted | dashed" lift>)
   */
  class BentoCard extends HTMLElement {
    static get observedAttributes() {
      return ["variant", "lift", "tilt"];
    }
    connectedCallback() {
      this.applyStyles();
    }
    attributeChangedCallback() {
      this.applyStyles();
    }
    applyStyles() {
      const variant = this.getAttribute("variant") || "light";
      this.classList.add("bento-card");
      this.classList.remove("bento-card--dark", "bento-card--light", "bento-card--muted", "bento-card--dashed");
      this.classList.add(`bento-card--${variant}`);

      if (this.hasAttribute("lift")) {
        this.classList.add("bento-lift");
      }
      if (this.hasAttribute("tilt")) {
        this.classList.add("bento-highlight-tilt");
      }
    }
  }

  /**
   * 3. CircularProgress Primitive (<circular-progress value="0" max="5" size="32" tone="light|dark">)
   */
  class CircularProgress extends HTMLElement {
    static get observedAttributes() {
      return ["value", "max", "size", "tone"];
    }
    connectedCallback() {
      this.render();
    }
    attributeChangedCallback() {
      this.render();
    }
    render() {
      const value = Math.max(0, Number(this.getAttribute("value") || 0));
      const max = Math.max(1, Number(this.getAttribute("max") || 5));
      const size = Number(this.getAttribute("size") || 32);
      const tone = this.getAttribute("tone") || "light";

      const strokeWidth = 2.6;
      const radius = (size - strokeWidth * 2) / 2;
      const circumference = 2 * Math.PI * radius;
      const ratio = Math.min(1, value / max);
      const offset = circumference * (1 - ratio);

      const trackColor = tone === "dark" ? "rgba(255,255,255,0.18)" : "#D2D4D9";
      const progressColor = tone === "dark" ? "#FFFFFF" : "#1E1E20";
      const textColor = tone === "dark" ? "#FFFFFF" : "#1E1E20";

      this.style.display = "inline-flex";
      this.style.alignItems = "center";
      this.style.justifyContent = "center";
      this.style.position = "relative";
      this.style.width = `${size}px`;
      this.style.height = `${size}px`;
      this.style.flexShrink = "0";

      this.innerHTML = `
        <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="transform: rotate(-90deg);">
          <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" fill="none" stroke="${trackColor}" stroke-width="${strokeWidth}"></circle>
          <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" fill="none" stroke="${progressColor}" stroke-width="${strokeWidth}" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" stroke-linecap="round" style="transition: stroke-dashoffset 0.35s cubic-bezier(0.22,1,0.36,1);"></circle>
        </svg>
        <span style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:9px; font-weight:700; color:${textColor}; letter-spacing:-0.03em; font-family:var(--font-mono);">${value}/${max}</span>
      `;
    }
  }

  /**
   * 4. AppShell & Sidebar Drawer Controller
   */
  const AppShell = {
    openDrawer() {
      const sidebar = document.getElementById("appSidebar");
      const backdrop = document.getElementById("mobileSidebarBackdrop");
      if (!sidebar || !backdrop) return;
      backdrop.classList.remove("hidden");
      requestAnimationFrame(() => {
        backdrop.classList.remove("opacity-0");
        sidebar.classList.remove("-translate-x-[120%]");
      });
    },
    closeDrawer() {
      const sidebar = document.getElementById("appSidebar");
      const backdrop = document.getElementById("mobileSidebarBackdrop");
      if (!sidebar || !backdrop) return;
      if (window.innerWidth >= 1024) return;
      sidebar.classList.add("-translate-x-[120%]");
      backdrop.classList.add("opacity-0");
      setTimeout(() => backdrop.classList.add("hidden"), 250);
    },
    toggleDrawer() {
      const sidebar = document.getElementById("appSidebar");
      if (!sidebar) return;
      if (sidebar.classList.contains("-translate-x-[120%]")) {
        this.openDrawer();
      } else {
        this.closeDrawer();
      }
    }
  };

  /**
   * 5. DarkContextMenu Controller
   */
  const DarkContextMenu = {
    closeAll() {
      document.querySelectorAll("[data-dark-menu]").forEach((menu) => {
        menu.classList.add("hidden");
      });
    },
    toggle(menuId, evt) {
      if (evt) evt.stopPropagation();
      const target = document.getElementById(menuId);
      if (!target) return;
      const isHidden = target.classList.contains("hidden");
      this.closeAll();
      if (isHidden) {
        target.classList.remove("hidden");
      }
    }
  };

  // Register custom elements once
  if (!customElements.get("svg-icon")) {
    customElements.define("svg-icon", SvgIcon);
  }
  if (!customElements.get("bento-card")) {
    customElements.define("bento-card", BentoCard);
  }
  if (!customElements.get("circular-progress")) {
    customElements.define("circular-progress", CircularProgress);
  }

  // Global listeners for menus & mobile drawer
  document.addEventListener("click", (e) => {
    if (!e.target.closest("[data-dark-menu]") && !e.target.closest("[data-dark-menu-trigger]")) {
      DarkContextMenu.closeAll();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      DarkContextMenu.closeAll();
      AppShell.closeDrawer();
    }
  });

  window.UIPrimitives = {
    AppShell,
    DarkContextMenu,
    ICON_PATHS
  };
})();
