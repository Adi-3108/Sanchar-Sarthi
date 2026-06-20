import React, { useState, useRef, useEffect } from "react";

export type SearchableSelectProps = {
  id?: string;
  name?: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  placeholder?: string;
  required?: boolean;
};

export function SearchableSelect({
  id,
  name,
  value,
  onChange,
  options,
  placeholder = "Select...",
  required = false
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Find the selected option to display its label
  const selectedOption = options.find((o) => o.value === value);
  const displayValue = selectedOption ? selectedOption.label : "";

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredOptions = options.filter((option) =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="relative w-full" ref={wrapperRef}>
      {/* Hidden input to ensure form validation and native form submission works */}
      <input type="hidden" name={name} value={value} required={required} />
      
      <div
        className={`flex min-h-[48px] w-full cursor-text items-center justify-between rounded-full border border-line/70 bg-bg/60 px-5 text-sm transition-colors hover:border-accent/40 ${isOpen ? "ring-2 ring-accent/30" : ""}`}
        onClick={() => setIsOpen(true)}
      >
        {isOpen ? (
          <input
            id={id}
            autoFocus
            className="w-full bg-transparent outline-none placeholder:text-muted"
            placeholder="Type to search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        ) : (
          <span className={`w-full truncate ${!displayValue ? "text-muted" : "text-copy"}`}>
            {displayValue || placeholder}
          </span>
        )}
        <div className="ml-2 flex items-center">
          <svg className={`h-4 w-4 text-muted transition-transform ${isOpen ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {isOpen && (
        <div className="absolute z-50 mt-2 max-h-60 w-full overflow-y-auto rounded-[20px] border border-line/70 bg-panel shadow-panel">
          {filteredOptions.length > 0 ? (
            <ul className="py-2">
              {filteredOptions.map((option) => (
                <li
                  key={option.value}
                  className={`cursor-pointer px-5 py-2.5 text-sm hover:bg-accent/10 ${value === option.value ? "bg-accent/15 font-medium text-accent" : "text-copy"}`}
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                    setSearchTerm("");
                  }}
                >
                  {option.label}
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-5 py-3 text-sm text-muted">No results found</div>
          )}
        </div>
      )}
    </div>
  );
}
