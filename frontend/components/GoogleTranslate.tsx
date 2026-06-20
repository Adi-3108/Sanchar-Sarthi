"use client";

import { useEffect } from "react";

const STORAGE_KEY = "sanchar_sarthi_language";

export default function GoogleTranslate() {
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) ?? "en";

    if (stored === "kn") {
      setCookie("googtrans", "/en/kn");
    } else {
      deleteCookie("googtrans");
    }

    // Inject an override stylesheet AFTER Google's own styles load
    // This ensures our rules win the specificity battle
    function injectOverrideCSS() {
      if (document.getElementById("gt-override-css")) return;
      const style = document.createElement("style");
      style.id = "gt-override-css";
      style.textContent = `
        /* Nuke the blue hover-box Google adds to translated words */
        .goog-text-highlight {
          background-color: transparent !important;
          background: transparent !important;
          box-shadow: none !important;
          border: none !important;
          outline: none !important;
        }
        /* Hide tooltip balloon that shows on hover */
        #goog-gt-tt, .goog-te-balloon-frame, .goog-tooltip,
        .goog-te-spinner-pos, .goog-te-spinner, .goog-te-banner-frame,
        .skiptranslate iframe {
          display: none !important;
          visibility: hidden !important;
        }
        /* Prevent body shift */
        body { top: 0px !important; margin-top: 0px !important; }
        body.translated-ltr, body.translated-rtl { top: 0px !important; margin-top: 0px !important; }
      `;
      // Append to END of head so it wins specificity over Google's styles
      document.head.appendChild(style);
    }

    (window as any).googleTranslateElementInit = function () {
      new (window as any).google.translate.TranslateElement(
        { pageLanguage: "en", includedLanguages: "kn", autoDisplay: false },
        "google_translate_element"
      );
      injectOverrideCSS();
    };

    if (!document.getElementById("google-translate-script")) {
      const script = document.createElement("script");
      script.id = "google-translate-script";
      script.src =
        "//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
      script.async = true;
      // Inject our CSS as soon as the script loads
      script.onload = injectOverrideCSS;
      document.body.appendChild(script);
    } else {
      injectOverrideCSS();
      if ((window as any).google?.translate) {
        (window as any).googleTranslateElementInit();
      }
    }

    // Keep body at top always
    const bodyFix = setInterval(() => {
      if (document.body.style.top && document.body.style.top !== "0px") {
        document.body.style.top = "0px";
        document.body.style.marginTop = "0px";
      }
    }, 500);

    return () => clearInterval(bodyFix);
  }, []);

  return (
    <div
      id="google_translate_element"
      aria-hidden="true"
      style={{
        position: "fixed",
        top: "-9999px",
        left: "-9999px",
        width: 0,
        height: 0,
        overflow: "hidden",
        opacity: 0,
        pointerEvents: "none",
      }}
    />
  );
}

function setCookie(name: string, value: string) {
  const domain = window.location.hostname;
  document.cookie = `${name}=${value}; path=/; domain=${domain}`;
  document.cookie = `${name}=${value}; path=/;`;
}

function deleteCookie(name: string) {
  const domain = window.location.hostname;
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${domain}`;
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}
