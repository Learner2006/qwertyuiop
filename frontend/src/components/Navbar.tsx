import React from "react";
import { APP_CONFIG } from "../config";
import { ShieldCheck, FileText, ArrowRight, Activity } from "lucide-react";

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
          {/* Patterned Star Logo in White */}
          <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-white shadow-xs group-hover:bg-slate-800 transition-colors">
            <svg
              className="w-5 h-5 text-white"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-label="Logo"
            >
              {/* Outer 4-point star silhouette */}
              <path
                d="M12 2L14.2 9.8L22 12L14.2 14.2L12 22L9.8 14.2L2 12L9.8 9.8Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              {/* Inner concentric geometric star pattern */}
              <path
                d="M12 6L13.5 10.5L18 12L13.5 13.5L12 18L10.5 13.5L6 12L10.5 10.5Z"
                stroke="currentColor"
                strokeWidth="1.2"
                strokeOpacity="0.7"
              />
              {/* Center core */}
              <circle cx="12" cy="12" r="1.5" fill="currentColor" />
              {/* Pattern ray lines connecting the geometry */}
              <path
                d="M12 2V6M12 18V22M2 12H6M18 12H22M6 6L8.5 8.5M18 6L15.5 8.5M6 18L8.5 15.5M18 18L15.5 15.5"
                stroke="currentColor"
                strokeWidth="1"
                strokeLinecap="round"
                strokeOpacity="0.5"
              />
            </svg>
          </div>
          <div>
            <span className="font-semibold text-lg text-slate-900 tracking-tight block">
              {APP_CONFIG.productName}
            </span>
            <span className="text-xs text-slate-500 font-mono">
              Elexon Replay · UTC
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
