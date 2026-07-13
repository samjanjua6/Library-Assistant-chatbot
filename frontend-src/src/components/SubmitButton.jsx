/**
 * SubmitButton — the ONLY element that carries the brand gradient.
 *
 * Design rule: accent gradient is restricted to primary CTAs only.
 * All other interactive elements (pill tabs, ghost buttons) use neutral tones.
 */
export default function SubmitButton({ children, loading }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className={[
        'w-full mt-2 py-3',
        'rounded-xl',
        'text-[0.93rem] font-semibold text-white',
        'bg-gradient-to-r from-indigo-500 to-violet-500',
        'shadow-[0_4px_20px_rgba(99,102,241,0.35)]',
        'transition-all duration-150',
        'hover:opacity-90 hover:-translate-y-px hover:shadow-[0_6px_28px_rgba(99,102,241,0.5)]',
        'active:translate-y-0 active:opacity-100',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:translate-y-0',
        'flex items-center justify-center gap-2',
      ].join(' ')}
    >
      {loading ? (
        <>
          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          <span>Loading…</span>
        </>
      ) : (
        children
      )}
    </button>
  )
}
