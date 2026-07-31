import { motion } from 'framer-motion'
import { Cpu, Terminal, Layers, Database, Sparkles } from 'lucide-react'

const glass = {
  background:    'var(--glass-bg)',
  border:        '1px solid var(--border)',
  
  
}

export default function TechSection() {
  const stack = [
    {
      category: "Backend Services",
      icon: <Terminal className="text-emerald-400" size={20} />,
      items: [
        { name: "FastAPI", desc: "High-performance async web framework built on Starlette and Pydantic." },
        { name: "SQLAlchemy 2.0", desc: "Next-gen Python SQL toolkit and Object Relational Mapper (ORM)." },
        { name: "WebSockets", desc: "Native full-duplex communication channel for instant message processing." }
      ]
    },
    {
      category: "Frontend Application",
      icon: <Layers className="text-indigo-400" size={20} />,
      items: [
        { name: "React 19", desc: "Declarative component-driven user interface with optimized state hydration." },
        { name: "Vite", desc: "Ultra-fast frontend build tool and hot module replacement dev server." },
        { name: "Tailwind CSS", desc: "Utility-first design framework leveraging custom CSS variables." }
      ]
    },
    {
      category: "Database & Inference",
      icon: <Cpu className="text-violet-400" size={20} />,
      items: [
        { name: "PostgreSQL", desc: "Robust open-source relational database to scale sessions and message logs." },
        { name: "Groq Cloud", desc: "Supercharged AI inference hardware to stream Llama response tokens in milliseconds." },
        { name: "Framer Motion", desc: "Production-ready animation library for React." }
      ]
    }
  ]

  return (
    <section id="tech" className="py-24 px-6 relative overflow-hidden">
      <div className="max-w-5xl mx-auto">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-xs font-semibold tracking-widest uppercase mb-3 bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
            Technology
          </h2>
          <h3 className="text-primary-500xl md:text-5xl font-bold tracking-tight mb-4" style={{ color: 'var(--text-primary-900)' }}>
            A Modern, Asynchronous Stack.
          </h3>
          <p className="text-md md:text-lg max-w-2xl mx-auto font-light leading-relaxed" style={{ color: 'var(--text-primary-700)' }}>
            Engineered with cutting-edge tools for fast, reactive, and reliable performance.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {stack.map((group, groupIdx) => (
            <motion.div
              key={groupIdx}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: groupIdx * 0.1, type: 'spring', stiffness: 100, damping: 15 }}
              style={{ ...glass }}
              className="p-8 rounded-3xl flex flex-col gap-6"
            >
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'var(--glass-hi)', border: '1px solid var(--border)' }}
                >
                  {group.icon}
                </div>
                <h4 className="font-bold text-lg" style={{ color: 'var(--text-primary-900)' }}>{group.category}</h4>
              </div>

              <div className="flex flex-col gap-5">
                {group.items.map((item, idx) => (
                  <div key={idx} className="flex flex-col gap-1 pl-1">
                    <h5 className="text-sm font-semibold flex items-center gap-2" style={{ color: 'var(--text-primary-900)' }}>
                      <Sparkles size={12} className="text-indigo-400 opacity-60" />
                      {item.name}
                    </h5>
                    <p className="text-xs font-light leading-relaxed pl-5" style={{ color: 'var(--text-primary-700)' }}>
                      {item.desc}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
