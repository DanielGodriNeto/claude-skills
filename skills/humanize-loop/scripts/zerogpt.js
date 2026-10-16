// Paste into the in-app browser's JavaScript tool on https://www.zerogpt.com/ (no login).
// Defines window.zr(text): fills the box, clicks "Detect Text", returns the API result:
//   { pct, flagged: [sentences], words }  (pct = word share of flagged sentences, repeatable).
// Only reads the page's own detector response; sends nothing anywhere else. Re-paste after a reload.
(() => {
  if (window.zr) return "already loaded";
  window.__zgResp = [];
  const isResult = (t) => /fakePercentage/.test(t);
  const origFetch = window.fetch;
  window.fetch = async (...args) => {
    const res = await origFetch(...args);
    res.clone().text().then((t) => isResult(t) && window.__zgResp.push(t)).catch(() => {});
    return res;
  };
  const origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function (...args) {
    this.addEventListener("load", () => {
      if (typeof this.responseText === "string" && isResult(this.responseText)) window.__zgResp.push(this.responseText);
    });
    return origSend.apply(this, args);
  };
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  window.zr = async (text) => {
    const box = document.querySelector("textarea");
    const button = [...document.querySelectorAll("button")].find((b) => /detect text/i.test(b.textContent));
    if (!box || !button) throw new Error("ZeroGPT page layout changed: textarea or Detect Text button not found");
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set.call(box, text);
    box.dispatchEvent(new Event("input", { bubbles: true }));  // React only sees the paste through this event
    const before = window.__zgResp.length;
    await sleep(300);
    button.click();
    for (let i = 0; i < 120; i++) {
      await sleep(500);
      if (window.__zgResp.length > before) {
        const d = JSON.parse(window.__zgResp.at(-1)).data;
        return { pct: d.fakePercentage, flagged: d.h, words: d.textWords };
      }
    }
    throw new Error("no detector response in 60 s (captcha, rate limit or layout change): stop, do not retry in a loop");
  };
  return "zr loaded";
})();
