const API_URL = `${window.API_BASE_URL}/generate-rental`;
const TOTAL_STEPS = 8;

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const form = document.getElementById("rental-form");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const submitBtn = document.getElementById("submit-btn");
const resultDiv = document.getElementById("result");
const stepProgress = document.getElementById("step-progress");
const monthlyRent = document.getElementById("monthly_rent");
const depositInput = document.getElementById("deposit");

let currentStep = 1;
let depositManual = false;

function initProgress() {
  stepProgress.innerHTML = "";
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    const dot = document.createElement("div");
    dot.className = "step-dot";
    dot.dataset.step = i;
    stepProgress.appendChild(dot);
  }
}

function showStep(step) {
  currentStep = step;
  form.querySelectorAll(".step-panel").forEach((panel) => {
    panel.classList.toggle("active", Number(panel.dataset.step) === step);
  });

  stepProgress.querySelectorAll(".step-dot").forEach((dot) => {
    const n = Number(dot.dataset.step);
    dot.classList.toggle("active", n === step);
    dot.classList.toggle("done", n < step);
  });

  prevBtn.disabled = step === 1;
  nextBtn.classList.toggle("hidden", step === TOTAL_STEPS);
  submitBtn.classList.toggle("hidden", step !== TOTAL_STEPS);
}

function isValidPassport(value) {
  const v = value.trim().toUpperCase();
  return /^[A-Z]{2}\d{7}$/.test(v) || /^[A-Z]{2}\s?\d{7}$/.test(v);
}

function normalizePassport(value) {
  return value.trim().toUpperCase().replace(/\s+/g, "");
}

function validateCurrentStep() {
  const panel = form.querySelector(`.step-panel[data-step="${currentStep}"]`);
  const inputs = panel.querySelectorAll("input, select, textarea");
  for (const input of inputs) {
    if (input.type === "radio" || input.type === "checkbox") continue;
    if (input.closest(".hidden")) continue;
    if (!input.checkValidity()) {
      input.reportValidity();
      return false;
    }
  }

  if (currentStep === 2) {
    if (!/^\d{14}$/.test(form.elements.landlord_pinfl.value.trim())) {
      alert("Ijaraga beruvchi JSHSHIR/PINFL 14 ta raqamdan iborat bo'lishi kerak.");
      return false;
    }
    const passport = form.elements.landlord_passport.value;
    if (!isValidPassport(passport)) {
      alert("Pasport formati noto'g'ri. Masalan: AA1234567");
      return false;
    }
  }

  if (currentStep === 3) {
    if (!/^\d{14}$/.test(form.elements.tenant_pinfl.value.trim())) {
      alert("Ijaraga oluvchi JSHSHIR/PINFL 14 ta raqamdan iborat bo'lishi kerak.");
      return false;
    }
    const passport = form.elements.tenant_passport.value;
    if (!isValidPassport(passport)) {
      alert("Pasport formati noto'g'ri. Masalan: AA1234567");
      return false;
    }
  }

  if (currentStep === 5) {
    if (checkedValues("payment_methods").length === 0) {
      alert("Kamida bitta to'lov usulini tanlang.");
      return false;
    }
    if (checkedValues("utilities_paid_by").length === 0) {
      alert("Kommunal to'lovlar kim tomonidan to'lanishini tanlang.");
      return false;
    }
    if (
      checkedValues("utilities_paid_by").includes("partial") &&
      !val("utilities_note")
    ) {
      alert("Qisman to'lov uchun izoh kiriting.");
      return false;
    }
  }

  return true;
}

function todayISO() {
  return new Date().toISOString().split("T")[0];
}

function syncDeposit() {
  if (depositManual) return;
  const rent = parseFloat(monthlyRent.value);
  if (!Number.isNaN(rent) && rent >= 0) {
    depositInput.value = rent.toFixed(2);
  }
}

function val(name) {
  const el = form.elements[name];
  if (!el) return "";
  return typeof el.value === "string" ? el.value.trim() : el.value;
}

function checkedValues(name) {
  return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map((el) => el.value);
}

function radioBool(name) {
  return form.querySelector(`input[name="${name}"]:checked`)?.value === "true";
}

function parseErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object") {
          const field = item.loc?.slice(-1)[0] || "maydon";
          return `${field}: ${item.msg}`;
        }
        return String(item);
      })
      .join("; ");
  }
  return "Xatolik yuz berdi, qayta urinib ko'ring";
}

function buildPayload() {
  const appliances = checkedValues("appliances");
  return {
    contract_number: val("contract_number"),
    contract_date: val("contract_date"),
    contract_place: val("contract_place"),
    rental_period: val("rental_period"),
    landlord: {
      full_name: val("landlord_full_name"),
      birth_date: val("landlord_birth_date"),
      passport: normalizePassport(val("landlord_passport")),
      pinfl: val("landlord_pinfl"),
      address: val("landlord_address"),
      phone: val("landlord_phone"),
      email: val("landlord_email"),
      property_document: val("landlord_property_doc"),
      workplace: "",
    },
    tenant: {
      full_name: val("tenant_full_name"),
      birth_date: val("tenant_birth_date"),
      passport: normalizePassport(val("tenant_passport")),
      pinfl: val("tenant_pinfl"),
      address: val("tenant_address"),
      phone: val("tenant_phone"),
      email: val("tenant_email"),
      property_document: "",
      workplace: val("tenant_workplace"),
    },
    property_address: val("property_address"),
    property_type: val("property_type"),
    total_area: parseFloat(val("total_area")),
    rooms_count: parseInt(val("rooms_count"), 10),
    floor: parseInt(val("floor"), 10),
    furnished: radioBool("furnished"),
    appliances,
    other_appliances: appliances.includes("Boshqa") ? val("other_appliances") : "",
    monthly_rent: parseFloat(val("monthly_rent")),
    currency: val("currency"),
    deposit: parseFloat(val("deposit")),
    payment_day: val("payment_day"),
    payment_methods: checkedValues("payment_methods"),
    utilities_paid_by: checkedValues("utilities_paid_by"),
    utilities_note: val("utilities_note"),
    penalty_percent: parseFloat(val("penalty_percent")) || 0.5,
    pets_allowed: form.querySelector('input[name="pets_allowed"]:checked')?.value || "Yo'q",
    guests_policy: form.querySelector('input[name="guests_policy"]:checked')?.value || "Ruxsat",
    smoking_policy: form.querySelector('input[name="smoking_policy"]:checked')?.value || "Yo'q",
    repairs_by: val("repairs_by"),
    max_repair_amount: val("max_repair_amount") ? parseFloat(val("max_repair_amount")) : null,
    deposit_return_terms: val("deposit_return_terms"),
    notice_days: parseInt(val("notice_days"), 10) || 30,
    early_termination_penalty: val("early_termination_penalty")
      ? parseFloat(val("early_termination_penalty"))
      : null,
    damage_liability: val("damage_liability"),
    electronic_signature: radioBool("electronic_signature"),
    witnesses_required: radioBool("witnesses_required"),
    witnesses_count: radioBool("witnesses_required")
      ? parseInt(val("witnesses_count"), 10) || 2
      : 0,
  };
}

function toggleHidden(triggerId, fieldId, showWhenChecked) {
  const trigger = document.getElementById(triggerId);
  const field = document.getElementById(fieldId);
  if (!trigger || !field) return;
  const update = () => {
    const on = showWhenChecked ? trigger.checked : trigger.value === "true" || trigger.checked;
    field.classList.toggle("hidden", !on);
  };
  trigger.addEventListener("change", update);
  update();
}

prevBtn.addEventListener("click", () => {
  if (currentStep > 1) showStep(currentStep - 1);
});

nextBtn.addEventListener("click", () => {
  if (!validateCurrentStep()) return;
  if (currentStep < TOTAL_STEPS) showStep(currentStep + 1);
});

monthlyRent.addEventListener("input", syncDeposit);

depositInput.addEventListener("input", () => {
  depositManual = true;
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!validateCurrentStep()) return;

  submitBtn.disabled = true;
  submitBtn.textContent = "Shartnoma tayyorlanmoqda...";
  resultDiv.className = "result hidden";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });

    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Backend bilan bog'lanib bo'lmadi. Backend ishga tushirilganini tekshiring.");
      }
      throw new Error(parseErrorDetail(result.detail) || `Server xatosi (${response.status})`);
    }

    resultDiv.className = "result success";
    resultDiv.innerHTML = `
      <strong>✅ Shartnoma muvaffaqiyatli yaratildi!</strong><br>
      Fayl: ${result.filename}<br>
      <a href="${result.download_url}" target="_blank" rel="noopener">📥 PDF yuklab olish</a>
    `;
    tg?.HapticFeedback?.notificationOccurred("success");
    resultDiv.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    resultDiv.className = "result error";
    resultDiv.innerHTML = `<strong>❌ Xatolik:</strong> ${err.message || "Xatolik yuz berdi, qayta urinib ko'ring"}`;
    tg?.HapticFeedback?.notificationOccurred("error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "📄 Shartnomani yaratish";
  }
});

toggleHidden("appliance-other-cb", "other-appliances-field", true);
toggleHidden("utilities-partial-cb", "utilities-note-field", true);

document.getElementById("witnesses-yes")?.addEventListener("change", () => {
  document.getElementById("witnesses-count-field")?.classList.toggle(
    "hidden",
    !radioBool("witnesses_required")
  );
});
form.querySelectorAll('input[name="witnesses_required"]').forEach((el) => {
  el.addEventListener("change", () => {
    document.getElementById("witnesses-count-field")?.classList.toggle(
      "hidden",
      !radioBool("witnesses_required")
    );
  });
});

initProgress();
document.getElementById("contract_date").value = todayISO();
document.getElementById("contract_number").value = `UI-${new Date().getFullYear()}-001`;
showStep(1);
