document.querySelectorAll("[data-budget-calculator]").forEach((calculator) => {
  const locale = calculator.dataset.locale || "en-US";
  const currency = calculator.dataset.currency || "USD";
  const fields = {
    budget: calculator.querySelector("[data-budget-total]"),
    days: calculator.querySelector("[data-budget-days]"),
    elapsed: calculator.querySelector("[data-budget-elapsed]"),
    spent: calculator.querySelector("[data-budget-spent]"),
  };
  const output = {
    daily: calculator.querySelector("[data-budget-daily]"),
    expected: calculator.querySelector("[data-budget-expected]"),
    variance: calculator.querySelector("[data-budget-variance]"),
    remaining: calculator.querySelector("[data-budget-remaining]"),
    status: calculator.querySelector("[data-budget-status]"),
    error: calculator.querySelector("[data-budget-error]"),
  };
  const messages = locale === "zh-Hant-HK"
    ? {
        invalid: "請輸入有效數字；已過日數不可大於月份日數。",
        ahead: "目前支出高於按日平均進度，請檢查原因及餘下每日所需金額。",
        behind: "目前支出低於按日平均進度，先檢查需求、資格及流量質素，再決定是否調整。",
        onPace: "目前支出接近按日平均進度。仍應配合有效查詢及業務結果判斷。",
        complete: "所選期間已完結；剩餘每日金額不再適用。",
      }
    : {
        invalid: "Enter valid numbers; elapsed days cannot exceed days in the period.",
        ahead: "Spend is ahead of the even daily pace. Review the cause and the required remaining daily amount.",
        behind: "Spend is behind the even daily pace. Check demand, eligibility, and traffic quality before adjusting.",
        onPace: "Spend is close to the even daily pace. Continue evaluating qualified outcomes, not spend alone.",
        complete: "The selected period is complete; a remaining daily amount no longer applies.",
      };
  const money = new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  });

  const update = () => {
    const budget = Number(fields.budget?.value);
    const days = Number(fields.days?.value);
    const elapsed = Number(fields.elapsed?.value);
    const spent = Number(fields.spent?.value);
    const invalid = !Number.isFinite(budget) || budget <= 0
      || !Number.isFinite(days) || days <= 0
      || !Number.isFinite(elapsed) || elapsed < 0 || elapsed > days
      || !Number.isFinite(spent) || spent < 0;

    if (output.error) output.error.hidden = !invalid;
    if (invalid) return;

    const daily = budget / days;
    const expected = daily * elapsed;
    const variance = spent - expected;
    const remainingDays = days - elapsed;
    const remaining = remainingDays > 0 ? Math.max(0, budget - spent) / remainingDays : 0;
    const tolerance = Math.max(daily, expected * 0.05);

    if (output.daily) output.daily.textContent = money.format(daily);
    if (output.expected) output.expected.textContent = money.format(expected);
    if (output.variance) output.variance.textContent = `${variance >= 0 ? "+" : "-"}${money.format(Math.abs(variance))}`;
    if (output.remaining) output.remaining.textContent = remainingDays > 0 ? money.format(remaining) : "—";
    if (output.status) {
      output.status.textContent = remainingDays === 0
        ? messages.complete
        : variance > tolerance
          ? messages.ahead
          : variance < -tolerance
            ? messages.behind
            : messages.onPace;
    }
  };

  calculator.addEventListener("input", update);
  update();
});
