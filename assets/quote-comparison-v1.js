(function () {
  "use strict";
  const modes = new Set(["fixed", "percentage", "hybrid"]);

  function scaled(value, maximum) {
    const text = String(value).trim();
    if (!/^\d+(?:\.\d{1,2})?$/.test(text)) throw new RangeError("Invalid decimal");
    const [whole, fraction = ""] = text.split(".");
    const result = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
    if (result > BigInt(maximum) * 100n) throw new RangeError("Out of range");
    return result;
  }

  function calculateQuote(media, months, quote) {
    if (!modes.has(quote.mode)) throw new RangeError("Invalid fee model");
    const count = Number(months);
    if (!String(months).trim() || !Number.isInteger(count) || count < 1 || count > 120) throw new RangeError("Invalid months");
    const spend = scaled(media, 1000000);
    const term = BigInt(count);
    const base = quote.mode === "percentage" ? 0n : scaled(quote.base, 1000000);
    const rate = quote.mode === "fixed" ? 0n : scaled(quote.rate, 100);
    const minimum = quote.mode === "fixed" ? 0n : scaled(quote.minimum, 1000000);
    const setup = scaled(quote.setup, 1000000);
    // Round the monthly percentage fee once, in cents, before multiplying months.
    const calculated = base + (spend * rate + 5000n) / 10000n;
    const monthlyFee = calculated > minimum ? calculated : minimum;
    return {
      monthlyFeeCents: Number(monthlyFee),
      firstMonthCents: Number(spend + monthlyFee + setup),
      serviceTotalCents: Number(monthlyFee * term + setup),
      termTotalCents: Number((spend + monthlyFee) * term + setup),
    };
  }

  if (typeof module !== "undefined" && module.exports) module.exports = { calculateQuote };
  if (typeof document === "undefined") return;

  document.querySelectorAll("[data-quote-comparison]").forEach((form, index) => {
    const fields = form.querySelector("[data-quote-fields]");
    const media = form.querySelector("[data-quote-media]");
    const months = form.querySelector("[data-quote-months]");
    const currency = form.querySelector("[data-quote-currency]");
    const error = form.querySelector("[data-quote-error]");
    const results = form.querySelector("[data-quote-results]");
    const quotes = [...form.querySelectorAll("[data-quote-offer]")];
    if (!fields || !media || !months || !currency || !error || !results || quotes.length !== 2) return;
    fields.disabled = false;
    form.querySelector('[type="reset"]').disabled = false;
    error.id = `quote-error-${index}`;
    form.querySelectorAll("input,select").forEach(field => field.setAttribute("aria-describedby", error.id));

    function update() {
      const offers = quotes.map(offer => {
        const value = name => offer.querySelector(`[data-quote-${name}]`);
        const mode = value("mode").value;
        ["base", "rate", "minimum"].forEach(name => {
          const field = value(name);
          field.disabled = name === "base" ? mode === "percentage" : mode === "fixed";
          field.closest("label").hidden = field.disabled;
        });
        return Object.fromEntries(["mode", "base", "rate", "minimum", "setup"].map(name => [name, value(name).value]));
      });
      const active = [...form.querySelectorAll("input,select")].filter(field => !field.disabled);
      const invalid = active.filter(field => {
        if (!field.checkValidity() || field.value.trim() === "") return true;
        if (field.type !== "number" || field === months) return false;
        try { scaled(field.value, Number(field.max)); return false; } catch (_) { return true; }
      });
      if (!["USD", "HKD"].includes(currency.value) && !invalid.includes(currency)) invalid.push(currency);
      let values;
      try {
        if (invalid.length) throw new RangeError("Invalid field");
        values = offers.map(quote => calculateQuote(media.value, months.value, quote));
      } catch (_) {
        values = null;
      }
      form.querySelectorAll("input,select").forEach(field => field.setAttribute("aria-invalid", String(invalid.includes(field))));
      error.hidden = Boolean(values);
      results.hidden = !values;
      if (!values) {
        results.querySelectorAll("output").forEach(output => { output.textContent = "—"; });
        return;
      }
      const formatter = new Intl.NumberFormat("zh-CN", { style: "currency", currency: currency.value });
      values.forEach((quote, i) => {
        Object.entries(quote).forEach(([name, amount]) => {
          form.querySelector(`[data-quote-output="${i}-${name}"]`).textContent = formatter.format(amount / 100);
        });
      });
      form.querySelector("[data-quote-difference]").textContent = formatter.format((values[1].termTotalCents - values[0].termTotalCents) / 100);
    }

    form.addEventListener("submit", event => event.preventDefault());
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    form.addEventListener("reset", () => setTimeout(update, 0));
    form.dataset.quoteReady = "true";
    form.querySelector("[data-quote-unavailable]").hidden = true;
    update();
  });
})();
