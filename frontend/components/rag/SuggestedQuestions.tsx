"use client";

export type SuggestedQuestionItem = {
  label: string;
  question: string;
};

export function SuggestedQuestions({
  items,
  disabled,
  onSelect,
}: {
  items: SuggestedQuestionItem[];
  disabled?: boolean;
  onSelect: (question: string) => void;
}) {
  if (!items.length) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <button
          key={item.label}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(item.question)}
          className="rounded-full border border-slate-700 bg-slate-900/60 px-3 py-2 text-left text-xs font-medium uppercase tracking-[0.18em] text-slate-200 transition hover:border-sky-400 hover:text-sky-200 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
