import React from "react";
import { APP_CONFIG } from "../config";
import { Wind, ShieldCheck, FileText, ArrowRight, Activity } from "lucide-react";

interface NavbarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentPath, onNavigate }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div
          onClick={() => onNavigate("/")}
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 group-hover:bg-sky-100 transition-colors">
            <Wind className="w-6 h-6" />
          </div>
          <div>
            <span className="font-semibold text-lg text-slate-900 tracking-tight block">
              {APP_CONFIG.productName}
            </span>
            <span className="text-xs text-slate-500 font-mono">
              Elexon BMRS Replay · UTC
            </span>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="hidden md:flex items-center space-x-1">
          <button
            onClick={() => onNavigate("/")}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              currentPath === "/"
                ? "bg-slate-100 text-slate-900 font-semibold"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => onNavigate("/jan25")}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-1.5 ${
              currentPath === "/jan25"
                ? "bg-sky-50 text-sky-800 font-semibold border border-sky-200"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            <Activity className="w-4 h-4 text-sky-600" />
            <span>Estimate</span>
          </button>
          <button
            onClick={() => onNavigate("/jan25/check")}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-1.5 ${
              currentPath === "/jan25/check"
                ? "bg-amber-50 text-amber-900 font-semibold border border-amber-200"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-amber-600" />
            <span>Reliability Check</span>
          </button>
          <button
            onClick={() => onNavigate("/docs")}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-1.5 ${
              currentPath === "/docs"
                ? "bg-slate-100 text-slate-900 font-semibold"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            <FileText className="w-4 h-4 text-slate-500" />
            <span>Methodology</span>
          </button>
        </nav>

        {/* CTA */}
        <div className="flex items-center space-x-3">
          {currentPath !== "/jan25" && (
            <button
              onClick={() => onNavigate("/jan25")}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-sky-600 hover:bg-sky-700 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500"
            >
              <span>Explore estimate</span>
              <ArrowRight className="ml-1.5 w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
