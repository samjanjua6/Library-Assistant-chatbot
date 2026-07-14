import { motion } from 'framer-motion'

/**
 * SubmitButton — the ONLY element that carries the brand gradient.
 * Design rule: the indigo→violet gradient is reserved for primary CTAs only.
 */
export default function SubmitButton({ children, loading }) {
  return (
    <motion.button
      whileHover={{ scale: 1.02, opacity: 0.92 }}
      whileTap={{ scale: 0.98 }}
      type="submit"
      disabled={loading}
      className="w-full mt-2 py-3 rounded-xl text-[0.93rem] font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      style={{
        background:  'linear-gradient(135deg, #3498DB, #2980B9)',
        boxShadow:   '0 4px 20px rgba(52, 152, 219, 0.35)',
      }}
    >
      {loading ? (
        <>
          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          <span>Loading…</span>
        </>
      ) : (
        children
      )}
    </motion.button>
  )
}
