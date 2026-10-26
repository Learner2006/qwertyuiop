import React, { useState } from "react";
import { EstimateResponse } from "../types";
import { ChevronDown, ChevronUp, HelpCircle } from "lucide-react";

interface EstimateFaqProps {
  estimateData: EstimateResponse;
}

export const EstimateFaq: React.FC<EstimateFaqProps> = ({ estimateData }) => {
  const [faqOpen, setFaqOpen] = useState<{ [key: string]: boolean }>({
    faq1: true,
    faq2: true,
    faq3: false,
    faq4: false,
  });

  const toggleFaq = (key: string) => {
    setFaqOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const {
    error_distribution,
    historical_observations_count,
    elexon_headline_gw,
    safe_headline_gw,
    selected_percentile = 75,
  } = estimateData;

  const appliedMargin = elexon_headline_gw - safe_headline_gw;
  const inSampleShortPct = Math.round(100 - selected_percentile);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 sm:p-8 space-y-6 shadow-sm">
      <div>
        <div className="inline-flex items-center space-x-1.5 text-xs font-mono font-bold uppercase tracking-wider text-sky-700">
          <HelpCircle className="w-3.5 h-3.5 text-sky-600" />
          <span>Buyer Q&A</span>
        </div>
        <h3 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
          How to Read This Page (FAQ)
        </h3>
        <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-3xl leading-relaxed">
          Clear answers to common questions about our methodology, the caution trade-off, and practical day-ahead planning.
        </p>
      </div>

      <div className="space-y-3 pt-2">
        {/* FAQ 1 */}
        <div className="border border-slate-200 rounded-xl overflow-hidden transition-colors">
          <button
            onClick={() => toggleFaq("faq1")}
            className="w-full flex items-center justify-between p-4 text-left font-bold text-slate-900 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-sm sm:text-base"
          >
            <span>1. Why is your estimate lower than Elexon's?</span>
            {faqOpen.faq1 ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
          </button>
          {faqOpen.faq1 && (
            <div className="p-4 bg-white text-xs sm:text-sm text-slate-700 leading-relaxed border-t border-slate-200 space-y-2">
              <p>
                Because Elexon's forecast ran above FUELHH outturn in <strong>{error_distribution ? `${error_distribution.overforecast_pct}%` : "100%"}</strong> of the last 48 hours
                ({error_distribution?.overforecast_count ?? historical_observations_count} of the last {historical_observations_count} half-hours), and this setting protects against the {selected_percentile}th signed-error percentile ({appliedMargin.toFixed(1)} GW).
              </p>
              <p className="text-slate-500 text-xs">
                When a buyer relies on unadjusted forecasts when forecasts run persistently above outturn, replacement power must be bought closer to delivery to cover the gap.
              </p>
            </div>
          )}
        </div>

        {/* FAQ 2 */}
        <div className="border border-slate-200 rounded-xl overflow-hidden transition-colors">
          <button
            onClick={() => toggleFaq("faq2")}
            className="w-full flex items-center justify-between p-4 text-left font-bold text-slate-900 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-sm sm:text-base"
          >
            <span>2. What happens to the difference?</span>
            {faqOpen.faq2 ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
          </button>
          {faqOpen.faq2 && (
            <div className="p-4 bg-white text-xs sm:text-sm text-slate-700 leading-relaxed border-t border-slate-200 space-y-2">
              <p>
                Each half-hour has its own forecast and its own deducted margin. If outturn wind in a half-hour falls below that half-hour's cautious plan, replacement power must be bought closer to delivery.
              </p>
              <p className="font-semibold text-slate-800">
                In the last 48 hours, this margin would still have left about {inSampleShortPct}% of half-hours short; tomorrow may differ.
              </p>
              <p className="text-slate-500 text-xs">
                When actual wind generation exceeds our plan, the difference represents surplus power arranged in advance. We do not model prices, so all results are shown in MWh.
              </p>
            </div>
          )}
        </div>

        {/* FAQ 3 */}
        <div className="border border-slate-200 rounded-xl overflow-hidden transition-colors">
          <button
            onClick={() => toggleFaq("faq3")}
            className="w-full flex items-center justify-between p-4 text-left font-bold text-slate-900 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-sm sm:text-base"
          >
            <span>3. Can I change the caution level?</span>
            {faqOpen.faq3 ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
          </button>
          {faqOpen.faq3 && (
            <div className="p-4 bg-white text-xs sm:text-sm text-slate-700 leading-relaxed border-t border-slate-200 space-y-2">
              <p>
                Yes. The slider lets you choose from <strong>p60</strong> (less buffer, lower advance power arranged) to <strong>p90</strong> (more protective buffer, higher advance power arranged).
              </p>
              <p className="text-slate-500 text-xs">
                The trade-off table above reveals what each setting would have cost in extra advance volume and saved in shortfall so far this month.
              </p>
            </div>
          )}
        </div>

        {/* FAQ 4 */}
        <div className="border border-slate-200 rounded-xl overflow-hidden transition-colors">
          <button
            onClick={() => toggleFaq("faq4")}
            className="w-full flex items-center justify-between p-4 text-left font-bold text-slate-900 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-sm sm:text-base"
          >
            <span>4. Is performance guaranteed? (No guarantee)</span>
            {faqOpen.faq4 ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
          </button>
          {faqOpen.faq4 && (
            <div className="p-4 bg-white text-xs sm:text-sm text-slate-700 leading-relaxed border-t border-slate-200 space-y-2">
              <p className="font-semibold text-slate-900">
                No, it is not guaranteed. This is a one-month historical replay (January 2026), and the margin can be wrong on any given day.
              </p>
              <p>
                The model derives an empirical buffer from recent forecast errors. If tomorrow experiences weather dynamics outside the previous 48 hours (such as an unpredicted calm front or rapid atmospheric shift), shortfalls can still occur.
              </p>
              <p className="text-slate-500 text-xs">
                By tracking historical errors empirically, buyers can reduce the frequency and severity of emergency replacement power, but cannot eliminate forecast uncertainty entirely.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};