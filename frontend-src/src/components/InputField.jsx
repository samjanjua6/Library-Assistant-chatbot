/**
 * InputField — a labeled text/email/password input.
 *
 * Styling decisions:
 * - Background: transparent-dark (bg-canvas), so it recedes into the card
 * - Border: subtle edge colour; turns indigo on focus (no glow noise elsewhere)
 * - Label: small, medium-weight, slate-400
 * - No icons, no decorations — pure minimal
 */
export default function InputField({ id, label, ...inputProps }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[0.82rem] font-medium text-slate-400">
        {label}
      </label>
      <input
        id={id}
        className={[
          'w-full px-4 py-3',
          'bg-canvas',
          'border border-edge',
          'rounded-xl',
          'text-[0.93rem] text-slate-100 placeholder-slate-600',
          'outline-none',
          'transition-[border-color,box-shadow] duration-150',
          'focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/10',
        ].join(' ')}
        {...inputProps}
      />
    </div>
  )
}
