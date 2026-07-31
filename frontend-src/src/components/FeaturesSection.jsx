import { motion } from 'framer-motion'
import { Zap, MessageSquare, Sidebar, SunMoon, Code2 } from 'lucide-react'

const glass = {
  background:    'var(--glass-bg)',
  border:        '1px solid var(--border)',
  
  
}

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100, damping: 15 } }
}

export default function FeaturesSection() {
  const features = [
    {
      icon: <Zap className="text-amber-400" size={24} />,
      title: "Real-time Messaging Engine",
      description: "Powered by full-duplex WebSockets for instant messaging. No polling, no lag, just real-time bawal conversation."
    },
    {
      icon: <MessageSquare className="text-indigo-400" size={24} />,
      title: "AI Contextual Titles",
      description: "Groq LLM engine automatically reads your opening message and generates a concise, relevant title for the chat session."
    },
    {
      icon: <Sidebar className="text-violet-400" size={24} />,
      title: "Multi-Session Sidebar",
      description: "Organize your workflow. Create new sessions, view history, or prune old sessions seamlessly with one-click cascade deletion."
    },
    {
      icon: <SunMoon className="text-pink-400" size={24} />,
      title: "Adaptive Theme Engine",
      description: "Fluid dark/light mode toggle with custom CSS variables, giving you smooth transitions that are easy on the eyes."
    },
    {
      icon: <Code2 className="text-emerald-400" size={24} />,
      title: "Clean SPA Architecture",
      description: "Modular React 19 codebase running on Vite with FastAPI backend. Extremely lightweight, responsive, and easy to extend."
    }
  ]

  return (
    <section id="features" className="py-24 px-6 relative overflow-hidden">
      <div className="max-w-5xl mx-auto">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-xs font-semibold tracking-widest uppercase mb-3 bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
            Features
          </h2>
          <h3 className="text-primary-500xl md:text-5xl font-bold tracking-tight mb-4" style={{ color: 'var(--text-primary-900)' }}>
            Engineered for Speed. <br className="hidden md:inline" />Crafted for Simplicity.
          </h3>
          <p className="text-md md:text-lg max-w-2xl mx-auto font-light leading-relaxed" style={{ color: 'var(--text-primary-700)' }}>
            A lightweight design that hides powerful features under the hood. Experience messaging the way it was meant to be.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feat, i) => (
            <motion.div
              key={i}
              variants={cardVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-50px" }}
              whileHover={{ y: -5, transition: { duration: 0.2 } }}
              style={{ ...glass }}
              className="p-8 rounded-3xl flex flex-col gap-4 cursor-default relative overflow-hidden group"
            >
              {/* Subtle ambient light on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              <div 
                className="w-12 h-12 rounded-2xl flex items-center justify-center"
                style={{ background: 'var(--glass-hi)', border: '1px solid var(--border)' }}
              >
                {feat.icon}
              </div>
              <h4 className="text-lg font-bold" style={{ color: 'var(--text-primary-900)' }}>{feat.title}</h4>
              <p className="text-sm font-light leading-relaxed" style={{ color: 'var(--text-primary-700)' }}>{feat.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
