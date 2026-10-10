(function () {
  const form = document.getElementById("briefForm");
  if (!form) return;
  const panels = [...form.querySelectorAll(".step-panel")];
  const stepLabels = [...document.querySelectorAll(".steps li")];
  let step = 0;

  function show(i) {
    step = Math.max(0, Math.min(panels.length - 1, i));
    panels.forEach((p, idx) => p.classList.toggle("active", idx === step));
    stepLabels.forEach((li, idx) => li.classList.toggle("active", idx === step));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  form.querySelectorAll("[data-next]").forEach((b) =>
    b.addEventListener("click", () => {
      const required = panels[step].querySelector("[data-required]");
      if (required && !required.value.trim()) {
        required.reportValidity();
        required.focus();
        return;
      }
      show(step + 1);
    })
  );
  form.querySelectorAll("[data-prev]").forEach((b) => b.addEventListener("click", () => show(step - 1)));
  stepLabels.forEach((li, idx) => li.addEventListener("click", () => show(idx)));

  const idea = document.getElementById("idea");
  const genBtn = document.getElementById("generateBrief");
  const status = document.getElementById("aiStatus");
  if (genBtn) {
    genBtn.addEventListener("click", async () => {
      status.textContent = "Shaping a structured brief…";
      genBtn.disabled = true;
      try {
        const res = await fetch("/api/ai-brief", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idea: idea.value }),
        });
        if (!res.ok) throw new Error("bad");
        const data = await res.json();
        const set = (name, val) => {
          const el = form.querySelector(`[name="${name}"]`);
          if (el && val != null) el.value = val;
        };
        set("title", data.title);
        set("description", data.campaign_objective);
        set("content_type", data.content_type);
        set("creative_goal", data.creative_goal);
        set("style", data.style);
        set("visual_direction", data.visual_direction);
        set("ai_requirements", data.ai_requirements);
        set("format", data.format);
        set("aspect_ratio", data.aspect_ratio);
        set("deliverables", data.deliverables);
        set("commercial_use", data.commercial_use);
        set("deadline", data.suggested_timeline);
        const aiFlag = form.querySelector('[name="ai_generated"]');
        if (aiFlag) aiFlag.value = "1";
        (data.suggested_skills || []).forEach((name) => {
          const box = form.querySelector(`input[name="skills"][value="${name}"]`);
          if (box) box.checked = true;
        });
        (data.suggested_tools || []).forEach((name) => {
          const box = form.querySelector(`input[name="tools"][value="${name}"]`);
          if (box) box.checked = true;
        });
        status.textContent =
          data.source === "live-api"
            ? "Filled from the connected AI provider. Review every field before publishing."
            : "Filled by the local intelligent layer (no API key). Review every field before publishing.";
        show(1);
      } catch (e) {
        status.textContent = "Could not generate. You can still complete the brief manually.";
      }
      genBtn.disabled = false;
    });
  }
})();
