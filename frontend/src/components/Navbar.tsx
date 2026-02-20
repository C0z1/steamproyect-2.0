import Link from 'next/link'
import { Gamepad2, Activity } from 'lucide-react'

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-40 glass border-b border-steam-border/50">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 rounded-lg bg-steam-cyan/10 border border-steam-cyan/20 flex items-center justify-center group-hover:bg-steam-cyan/20 transition-colors">
            <Gamepad2 size={14} className="text-steam-cyan" />
          </div>
          <span className="font-display font-bold text-steam-text text-sm tracking-wide">
            Steam<span className="text-steam-cyan">Sense</span>
          </span>
        </Link>

        <div className="flex items-center gap-4 text-xs text-steam-subtle font-mono">
          <Link href="/" className="hover:text-steam-text transition-colors">Search</Link>
          <div className="w-px h-3 bg-steam-border" />
          <div className="flex items-center gap-1.5">
            <Activity size={11} className="text-steam-green" />
            <span className="text-steam-green">Live</span>
          </div>
        </div>
      </div>
    </nav>
  )
}
