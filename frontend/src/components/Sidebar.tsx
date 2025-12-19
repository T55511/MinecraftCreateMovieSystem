'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar() {
  const pathname = usePathname();
  const menus = [
    { name: 'Dashboard', href: '/', icon: '🏠' },
    { name: 'Planner', href: '/planner', icon: '💡' },
    { name: 'Studio', href: '/studio', icon: '🎙️' },
    { name: 'Analytics', href: '/analytics', icon: '📊' },
  ];

  return (
    <div className="w-64 h-screen bg-slate-900 text-white fixed left-0 top-0 p-6 flex flex-col shadow-2xl">
      <div className="text-2xl font-black mb-10 text-emerald-400 tracking-tighter">
        RADIO FLOW
      </div>
      <nav className="flex-1">
        {menus.map((m) => (
          <Link 
            key={m.href} 
            href={m.href} 
            className={`flex items-center p-3 mb-2 rounded-xl transition-all ${
              pathname === m.href ? 'bg-emerald-600 text-white' : 'hover:bg-slate-800 text-slate-400'
            }`}
          >
            <span className="mr-3 text-xl">{m.icon}</span>
            <span className="font-bold">{m.name}</span>
          </Link>
        ))}
      </nav>
      {/* 習慣化サポート表示（仕様書の負荷表示） */}
      <div className="mt-auto p-4 bg-slate-800 rounded-2xl border border-slate-700">
        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-2">Weekly Load</div>
        <div className="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
          <div className="bg-emerald-500 h-full w-[75%] shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
        </div>
        <div className="text-right text-[10px] mt-2 text-emerald-400 font-mono">75% BUSY</div>
      </div>
    </div>
  );
}