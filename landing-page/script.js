(function () {
  "use strict";

  // ---------------------------------------------------------
  // Config — troque pelos dados reais antes de publicar
  // ---------------------------------------------------------
  var CONFIG = {
    whatsappNumber: "5500000000000", // formato: DDI+DDD+número, só dígitos
  };

  function buildWhatsAppLink(message) {
    var text = encodeURIComponent(message || "Olá! Vi a página e quero saber mais.");
    return "https://wa.me/" + CONFIG.whatsappNumber + "?text=" + text;
  }

  document.querySelectorAll(".wa-link").forEach(function (el) {
    el.setAttribute("href", buildWhatsAppLink(el.getAttribute("data-wa-message")));
  });

  // ---------------------------------------------------------
  // Mobile nav drawer
  // ---------------------------------------------------------
  var drawer = document.getElementById("mobileDrawer");
  var navToggle = document.getElementById("navToggle");
  var navClose = document.getElementById("navClose");

  function openDrawer() {
    drawer.setAttribute("data-open", "true");
    navToggle.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
    navClose.focus();
  }

  function closeDrawer() {
    drawer.setAttribute("data-open", "false");
    navToggle.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
    navToggle.focus();
  }

  if (navToggle) {
    navToggle.addEventListener("click", openDrawer);
    navClose.addEventListener("click", closeDrawer);
    drawer.querySelectorAll(".drawer-link").forEach(function (link) {
      link.addEventListener("click", closeDrawer);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && drawer.getAttribute("data-open") === "true") {
        closeDrawer();
      }
    });
  }

  // ---------------------------------------------------------
  // FAQ accordion
  // ---------------------------------------------------------
  document.querySelectorAll(".faq-item").forEach(function (item) {
    var question = item.querySelector(".faq-question");
    question.addEventListener("click", function () {
      var isOpen = item.getAttribute("data-open") === "true";
      item.setAttribute("data-open", String(!isOpen));
      question.setAttribute("aria-expanded", String(!isOpen));
    });
  });

  // ---------------------------------------------------------
  // Calculadora
  // ---------------------------------------------------------
  var visitorsInput = document.getElementById("visitors");
  var currentInput = document.getElementById("current");
  var visitorsValue = document.getElementById("visitorsValue");
  var currentValue = document.getElementById("currentValue");
  var currentRateEl = document.getElementById("currentRate");
  var simulatedRateEl = document.getElementById("simulatedRate");

  function formatNumber(n) {
    return n.toLocaleString("pt-BR");
  }

  function formatPercent(n) {
    return n.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "%";
  }

  function updateCalculator() {
    var visitors = parseInt(visitorsInput.value, 10);
    var current = parseInt(currentInput.value, 10);

    visitorsValue.textContent = formatNumber(visitors);
    currentValue.textContent = formatNumber(current);

    var currentRate = visitors > 0 ? (current / visitors) * 100 : 0;
    // Multiplicador ilustrativo: um sistema de captação bem construído costuma
    // triplicar a taxa de conversão de tráfego que já existe, com teto realista de 8%.
    var simulatedRate = Math.min(currentRate * 3, 8);
    if (current === 0) {
      simulatedRate = Math.min(2.5, 8);
    }

    currentRateEl.textContent = formatPercent(currentRate);
    simulatedRateEl.textContent = formatPercent(simulatedRate);
  }

  if (visitorsInput && currentInput) {
    visitorsInput.addEventListener("input", updateCalculator);
    currentInput.addEventListener("input", updateCalculator);
    updateCalculator();
  }

  // ---------------------------------------------------------
  // Reveal on scroll
  // ---------------------------------------------------------
  var revealEls = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window && revealEls.length) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach(function (el) {
      observer.observe(el);
    });
  } else {
    revealEls.forEach(function (el) {
      el.classList.add("is-visible");
    });
  }
})();
