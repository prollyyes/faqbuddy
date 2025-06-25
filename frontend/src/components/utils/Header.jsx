'use client'

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import BackButton from './BackButton';

export default function Header() {
  const pathname = usePathname();

  const showBackButton =
    pathname.startsWith('/profile/') ||
    pathname === '/homepage/materials/research' ||
    pathname === '/homepage/materials/upload';

  const backHref = pathname.startsWith('/profile/')
    ? '/homepage/chat'
    : '/homepage/materials';

  return (
    <header className="w-full h-20 flex items-center justify-center text-[#822433] pt-2 fixed top-0 bg-white z-50 shadow-sm">
      {showBackButton && (
        <div className="absolute left-6 top-8">
          <BackButton href={backHref} />
        </div>
      )}
      <Link href="/homepage/chat" className="text-4xl font-bold tracking-wider mr-2">
        FAQBuddy
      </Link>
    </header>
  );
}
