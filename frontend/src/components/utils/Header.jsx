'use client'

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import BackButton from './BackButton';
import Image from 'next/image';

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
    <header className="w-full h-20 flex items-center justify-center text-[#822433] px-4 fixed top-0 bg-white z-50 shadow-sm">
      {/* {showBackButton && (
        <div className="absolute left-6 top-8">
          <BackButton href={backHref} />
        </div>
      )} */}
      <Link href="/homepage/chat" className="flex items-center" aria-label="Vai alla home">
        <Image
          src="/images/header_logo.png"
          alt="FAQBuddy"
          width={200}
          height={200}
          priority
          className="object-contain"
        />
      </Link>
    </header>
  );
}
