import { Info } from 'lucide-react'
import clsx from 'clsx'

/**
 * Accessible inline help — an info glyph that reveals a one-line explanation on
 * hover and keyboard focus. The text lives in aria-label so screen readers get
 * it too; the visual tooltip is decorative (aria-hidden). `align` keeps the
 * bubble from clipping the viewport edge for right-anchored labels.
 */
export function InfoHint({ text, align = 'center', className }) {
  return (
    <span className={clsx('relative inline-flex group align-middle', className)}>
      <button
        type="button"
        aria-label={text}
        className="text-subtext/70 hover:text-brand focus:text-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 rounded-full"
      >
        <Info className="w-3 h-3" />
      </button>
      <span
        aria-hidden="true"
        className={clsx(
          'pointer-events-none absolute bottom-full mb-1.5 w-max max-w-[220px] rounded-md',
          'bg-text text-white text-[10px] leading-snug px-2 py-1.5 shadow-md z-tooltip',
          'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-150',
          align === 'right' ? 'right-0' : 'left-1/2 -translate-x-1/2'
        )}
      >
        {text}
      </span>
    </span>
  )
}
