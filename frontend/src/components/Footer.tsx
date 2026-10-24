import React from "react";
import { APP_CONFIG } from "../config";
import { ShieldAlert } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-slate-200 mt-20 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 tracking-wider uppercase mb-3">
              {APP_CONFIG.productName}
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              {APP_CONFIG.pitch}
            </p>
            <div className="mt-3 inline-flex items-center text-xs text-slate-500 font-mono bg-slate-50 px-2.5 py-1 rounded border border-slate-200">
              Data standard: UTC throughout
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-900 tracking-wider uppercase mb-3">
              Data Governance
            </h3>
            <ul className="text-sm text-slate-600 space-y-2">
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
                <span>Source: Elexon BMRS WINDFOR (Forecast)</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>Source: Elexon BMRS FUELHH (Actual Wind)</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                <span>No future data leakage (09:00 UTC cutoff)</span>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-900 tracking-wider uppercase mb-3 flex items-center space-x-1.5">
              <ShieldAlert className="w-4 h-4 text-amber-500" />
              <span>Strict Disclosures</span>
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Historical replay for January 2026. This application is an energy risk analysis tool and does not provide financial advice, trading signals, or cash savings guarantees. Electricity prices and imbalance charges are outside project scope.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400">
          <p>© 2026 {APP_CONFIG.productName}. Built for rigorous verification and reproducibility.</p>
          <p className="mt-2 sm:mt-0 font-mono">Status: Ready · Parquet Cached</p>
        </div>
      </div>
    </footer>
  );
};
