'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Gamepad2, Compass, Activity } from 'lucide-react'

export default function Navbar() {
  const pathname = usePathname()

  const links = [
    { href: '/',        label: 'Search'  },
    { href: '/explore', label: 'Explore' },
  ]

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

        <div className="flex items-center gap-1">
          {links.map(({ href, label }) => {
            const active = href === '/' ? pathname === '/' : pathname.startsWith(href)
            return (
              <Link
                key={href}
                href={href}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                  active
                    ? 'bg-steam-cyan/10 text-steam-cyan'
                    : 'text-steam-subtle hover:text-steam-text hover:bg-steam-muted'
                }`}
              >
                {label}
              </Link>
            )
          })}
          <div className="ml-3 flex items-center gap-1.5 text-steam-subtle text-xs font-mono border-l border-steam-border pl-3">
            <Activity size={10} className="text-steam-green" />
            <span className="text-steam-green">Live</span>
          </div>
        </div>
      </div>
    </nav>
  )
}
