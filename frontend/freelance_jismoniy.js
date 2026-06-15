const API_URL = `${window.API_BASE_URL}/generate-mobile-app`;

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const form = document.getElementById("freelance-jismoniy-form");
const submitBtn = document.getElementById("submit-btn");
const resultDiv = document.getElementById("result");
const defaultBtnText = submitBtn.textContent;

const totalAmount = document.getElementById("total_amount");
const advancePercent = document.getElementById("advance_percent");
const finalPercent = document.getElementById("final_percent");
const advanceAmount = document.getElementById("advance_amount");
const finalAmount = document.getElementById("final_amount");

function todayISO() {
  return new Date().toISOString().split("T")[0];
}

function initDefaults() {
  document.getElementById("contract_date").value = todayISO();
  document.getElementById("contract_number").value = `FJ-${new Date().getFullYear()}-001`;
  recalcPayments();
}

function recalcPayments() {
  const total = parseFloat(totalAmount.value) || 0;
  const advPct = parseFloat(advancePercent.value) || 0;
  const finPct = parseFloat(finalPercent.value) || 0;
  advanceAmount.value = ((total * advPct) / 100).toFixed(2);
  finalAmount.value = ((total * finPct) / 100).toFixed(2);
}

[totalAmount, advancePercent, finalPercent].forEach((el) => {
  el.addEventListener("input", recalcPayments);
});

function val(name) {
  const el = form.elements[name];
  if (!el) return "";
  return typeof el.value === "string" ? el.value.trim() : el.value;
}

function checkedValues(name) {
  return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map((el) => el.value);
}

function radioBool(name) {
  const el = form.querySelector(`input[name="${name}"]:checked`);
  return el?.value === "true";
}

function checkboxBool(name) {
  const el = form.querySelector(`input[name="${name}"]`);
  return el ? el.checked : false;
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

function validateForm() {
  if (!form.checkValidity()) {
    form.reportValidity();
    return false;
  }
  if (checkedValues("project_types").length === 0) {
    alert("Kamida bitta loyiha turini tanlang.");
    return false;
  }
  if (checkedValues("payment_methods").length === 0) {
    alert("Kamida bitta to'lov usulini tanlang.");
    return false;
  }
  return true;
}

function buildPayload() {
  return {
    client: {
      full_name: val("client_full_name"),
      birth_date: val("client_birth_date"),
      passport: val("client_passport"),
      pinfl: val("client_pinfl"),
      address: val("client_address"),
      phone: val("client_phone"),
      email: val("client_email"),
      bank_details: val("client_bank"),
    },
    executor: {
      full_name: val("executor_full_name"),
      birth_date: val("executor_birth_date"),
      passport: val("executor_passport"),
      pinfl: val("executor_pinfl"),
      address: val("executor_address"),
      phone: val("executor_phone"),
      email: val("executor_email"),
      bank_details: val("executor_bank"),
    },
    project_name: val("project_name"),
    project_types: checkedValues("project_types"),
    project_description: val("project_description"),
    technical_spec: val("technical_spec"),
    start_date: val("start_date"),
    end_date: val("end_date"),
    duration_days: parseInt(val("duration_days"), 10),
    total_amount: parseFloat(val("total_amount")),
    currency: val("currency"),
    advance_percent: parseFloat(val("advance_percent")) || 30,
    advance_amount: parseFloat(val("advance_amount")) || 0,
    final_percent: parseFloat(val("final_percent")) || 70,
    final_amount: parseFloat(val("final_amount")) || 0,
    payment_methods: checkedValues("payment_methods"),
    penalty_percent: parseFloat(val("penalty_percent")) || 0.1,
    share_percent: parseFloat(val("share_percent")) || 15,
    share_years: parseInt(val("share_years"), 10) || 3,
    report_period: val("report_period"),
    share_payment_date: val("share_payment_date"),
    warranty_months: parseInt(val("warranty_months"), 10) || 12,
    free_updates: parseInt(val("free_updates"), 10) || 3,
    response_days: parseInt(val("response_days"), 10) || 3,
    ip_code_after_payment: checkboxBool("ip_code_after_payment"),
    ip_rights_until_payment: checkboxBool("ip_rights_until_payment"),
    ip_github: checkboxBool("ip_github"),
    ip_source_code: checkboxBool("ip_source_code"),
    ip_database: checkboxBool("ip_database"),
    ip_readme: checkboxBool("ip_readme"),
    nda_required: radioBool("nda_required"),
    nda_years: parseInt(val("nda_years"), 10) || 3,
    acceptance_days: parseInt(val("acceptance_days"), 10) || 10,
    fix_days: parseInt(val("fix_days"), 10) || 5,
    contract_number: val("contract_number"),
    contract_date: val("contract_date"),
    contract_place: val("contract_place"),
    electronic_signature: radioBool("electronic_signature"),
  };
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!validateForm()) return;

  submitBtn.disabled = true;
  submitBtn.textContent = "Shartnoma tayyorlanmoqda...";
  resultDiv.className = "result hidden";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });

    const result = await response.json();
    if (!response.ok) throw new Error(parseErrorDetail(result.detail));

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
    const msg = err.message === "Failed to fetch"
      ? "Server bilan bog'lanib bo'lmadi. Render backend uyg'onguncha 30-60 soniya kutib, qayta urinib ko'ring."
      : (err.message || "Xatolik yuz berdi, qayta urinib ko'ring");
    resultDiv.innerHTML = `<strong>❌ Xatolik:</strong> ${msg}`;
    tg?.HapticFeedback?.notificationOccurred("error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = defaultBtnText;
  }
});

initDefaults();
