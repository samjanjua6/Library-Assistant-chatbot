import { motion } from 'framer-motion'
import { ShieldAlert, KeyRound, Lock, Trash2, CheckCircle2 } from 'lucide-react'

const glass = {
  background:    'var(--glass-bg)',
  border:        '1px solid var(--border)',
  
  
}

export default function SecuritySection() {
  const points = [
    {
      icon: <KeyRound className="text-indigo-400" size={20} />,
      title: "Stateless JWT Auth Verification",
      description: "Signed using cryptographic secrets, validating every incoming client request and keeping routes completely airtight."
    },
    {
      icon: <Lock className="text-violet-400" size={20} />,
      title: "OAuth 2.0 Integration",
      description: "Secure one-click Sign In with Google. Credentials are authenticated directly via Google without storing passwords."
    },
    {
      icon: <Trash2 className="text-red-400" size={20} />,
      title: "Cascade Session Pruning",
      description: "Database cascade rules cleanly remove orphan messages whenever a session is deleted, leaving no data leaks."
    },
    {
      icon: <ShieldAlert className="text-pink-400" size={20} />,
      title: "Strict CORS & WebSocket Protocol",
      description: "Handshakes are rejected instantly if authorization parameters or origin headers are missing or spoofed."
    }
  ]

  return (
    <section id="security" className="py-24 px-6 relative overflow-hidden">
      <div className="max-w-5xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Text */}
          <motion.div 
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-5 flex flex-col gap-5"
          >
            <h2 className="text-xs font-semibold tracking-widest uppercase bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
              Security
            </h2>
            <h3 className="text-primary-500xl md:text-4xl font-bold tracking-tight" style={{ color: 'var(--text-primary-900)' }}>
              Protected by Enterprise-Grade Security.
            </h3>
            <p className="text-sm md:text-base font-light leading-relaxed" style={{ color: 'var(--text-primary-700)' }}>
              Your conversations are private and secured using stateless tokens, strict authentication scopes, and clean data cascade pruning rules.
            </p>
            <div className="flex flex-col gap-3 mt-2">
              {["No plain-text passwords", "One-click OAuth 2.0 tokens", "Automatic data cleaning"].map((text, idx) => (
                <div key={idx} className="flex items-center gap-2 text-sm font-medium" style={{ color: 'var(--text-primary-900)' }}>
                  <CheckCircle2 size={16} className="text-emerald-400" />
                  {text}
                </div>
              ))}
            </div>
          </motion.div>

          {/* Right Cards List */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            {points.map((point, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ delay: idx * 0.1, type: 'spring', stiffness: 100, damping: 15 }}
                style={{ ...glass }}
                className="p-6 rounded-3xl flex gap-5 items-start hover:bg-black/5 dark:hover:bg-white transition-all duration-300"
              >
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'var(--glass-hi)', border: '1px solid var(--border)' }}
                >
                  {point.icon}
                </div>
                <div className="flex flex-col gap-1">
                  <h4 className="text-sm font-bold" style={{ color: 'var(--text-primary-900)' }}>{point.title}</h4>
                  <p className="text-xs font-light leading-relaxed" style={{ color: 'var(--text-primary-700)' }}>{point.description}</p>
                </div>
              </motion.div>
            ))}
          </div>

        </div>
      </div>
    </section>
  )
}
