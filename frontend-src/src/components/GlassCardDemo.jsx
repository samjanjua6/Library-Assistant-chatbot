import React from 'react';
import { motion } from 'framer-motion';

export default function GlassCardDemo() {
  return (
    // 1. Animated Mesh Background container
    <div className="relative min-h-screen w-full bg-slate-950 overflow-hidden flex items-center justify-center font-sans">
      
      {/* 
        Floating Orbs using Framer Motion 
        We use varying durations and paths to make it feel organic.
      */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/30 rounded-full blur-[100px] pointer-events-none"
        animate={{
          x: [0, 100, -50, 0],
          y: [0, -100, 50, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.div
        className="absolute top-1/3 right-1/4 w-[28rem] h-[28rem] bg-blue-600/30 rounded-full blur-[100px] pointer-events-none"
        animate={{
          x: [0, -120, 80, 0],
          y: [0, 90, -70, 0],
        }}
        transition={{
          duration: 18,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.div
        className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-indigo-600/30 rounded-full blur-[100px] pointer-events-none"
        animate={{
          x: [0, 70, -90, 0],
          y: [0, 120, -50, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* 2. Crisp Glassmorphism Card (Foreground) */}
      <motion.div
        whileHover={{ y: -5 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
        className="
          relative z-10 w-full max-w-md p-8 rounded-3xl
          bg-white/5 backdrop-blur-xl
          border border-white/20
          shadow-[inset_0_1px_1px_rgba(255,255,255,0.4),0_8px_32px_rgba(0,0,0,0.5)]
        "
      >
        <div className="flex flex-col gap-4">
          {/* Subtle icon/accent at the top */}
          <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center border border-white/10 mb-2">
            <svg className="w-6 h-6 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>

          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Premium Experience
          </h2>
          
          <p className="text-slate-300 leading-relaxed font-medium">
            Experience the future of interface design with this animated glassmorphism component. The rim lighting and specular highlights create a physically accurate glass effect.
          </p>
          
          <button className="mt-4 py-3 px-6 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold border border-white/10 transition-colors">
            Get Started
          </button>
        </div>
      </motion.div>
    </div>
  );
}
