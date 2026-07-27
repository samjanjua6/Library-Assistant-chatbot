import AnimatedMeshBackground from '../components/AnimatedMeshBackground'
import FloatingNav from '../components/FloatingNav'
import Hero from '../components/Hero'
import FeaturesSection from '../components/FeaturesSection'
import TechSection from '../components/TechSection'
import SecuritySection from '../components/SecuritySection'

export default function LandingPage() {
  return (
    <div className="relative min-h-screen font-sans text-white">
      <AnimatedMeshBackground />

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
