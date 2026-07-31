/**
 * InputField — a labeled text/email/password input.
 * Colours driven entirely by CSS variables so dark ↔ light works automatically.
 */
export default function InputField({ id, label, ...inputProps }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="text-[0.82rem] font-medium"
        style={{ color: 'var(--text-primary-700)' }}
      >
        {label}
      </label>
      <input
        id={id}
        style={{
          background:    'var(--glass-input)',
          border:        '1px solid var(--border)',
          color:         'var(--text-primary-900)',
        }}
        className="w-full px-4 py-3 rounded-xl text-[0.93rem] outline-none placeholder:opacity-40 transition-all duration-150 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400/50"
        {...inputProps}
      />
    </div>
  )
}
