import { motion } from 'framer-motion'
import FloatingNav from '../components/FloatingNav'
import Hero from '../components/Hero'
import FeaturesSection from '../components/FeaturesSection'
import TechSection from '../components/TechSection'
import SecuritySection from '../components/SecuritySection'

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-slate-950 font-sans text-white">
      {/* Global Animated Mesh Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <motion.div
          className="absolute top-[10%] left-[20%] w-[40rem] h-[40rem] bg-purple-600/20 rounded-full blur-[120px]"
          animate={{ x: [0, 100, -50, 0], y: [0, -100, 50, 0] }}
          transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute top-[30%] right-[10%] w-[45rem] h-[45rem] bg-blue-600/20 rounded-full blur-[120px]"
          animate={{ x: [0, -120, 80, 0], y: [0, 90, -70, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute bottom-[-10%] left-[30%] w-[35rem] h-[35rem] bg-indigo-600/20 rounded-full blur-[120px]"
          animate={{ x: [0, 70, -90, 0], y: [0, 120, -50, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <FloatingNav />
      <main className="relative z-10 space-y-12">
        <Hero />
        <FeaturesSection />
        <TechSection />
        <SecuritySection />
      </main>
    </div>
  )
}
